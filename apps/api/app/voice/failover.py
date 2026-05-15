import asyncio
import time
from typing import Optional, Dict, List, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import random


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ServiceEndpoint:
    name: str
    url: str
    priority: int = 1
    timeout_ms: int = 5000
    max_retries: int = 3


@dataclass
class HealthCheckResult:
    service_name: str
    status: ServiceStatus
    latency_ms: float
    timestamp: float
    error: Optional[str] = None


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 30.0
    half_open_max_calls: int = 3


@dataclass
class CircuitBreaker:
    name: str
    state: CircuitState = CircuitState.CLOSED
    failures: int = 0
    successes: int = 0
    last_failure_time: float = 0.0
    half_open_calls: int = 0
    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    
    def record_success(self):
        self.successes += 1
        if self.state == CircuitState.HALF_OPEN:
            if self.successes >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failures = 0
                self.successes = 0
        elif self.state == CircuitState.CLOSED:
            self.failures = max(0, self.failures - 1)
    
    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.half_open_calls = 0
        elif self.state == CircuitState.CLOSED:
            if self.failures >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
        elif self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.config.timeout_seconds:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
    
    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.config.half_open_max_calls
        elif self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.config.timeout_seconds:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return False
    
    def increment_half_open(self):
        self.half_open_calls += 1


@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay_ms: int = 100
    max_delay_ms: int = 5000
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class FailoverEvent:
    timestamp: float
    event_type: str
    service_name: str
    details: Dict[str, Any]


class FailoverManager:
    def __init__(self):
        self.services: Dict[str, List[ServiceEndpoint]] = {}
        self.health_status: Dict[str, ServiceStatus] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_configs: Dict[str, RetryConfig] = {}
        self._event_history: deque = deque(maxlen=100)
        self._latency_history: Dict[str, deque] = {}
        self._consecutive_failures: Dict[str, int] = {}
        
        self._initialize_default_services()
    
    def _initialize_default_services(self):
        self.register_service("stt", [
            ServiceEndpoint("google_stt", "https://speech.googleapis.com", priority=1),
            ServiceEndpoint("elevenlabs_stt", "https://api.elevenlabs.io", priority=2),
            ServiceEndpoint("azure_stt", "https://speech.azure.com", priority=3),
        ])
        
        self.register_service("tts", [
            ServiceEndpoint("google_tts", "https://texttospeech.googleapis.com", priority=1),
            ServiceEndpoint("elevenlabs_tts", "https://api.elevenlabs.io", priority=2),
            ServiceEndpoint("azure_tts", "https://speech.azure.com", priority=3),
        ])
        
        self.register_service("llm", [
            ServiceEndpoint("gemini", "https://generativelanguage.googleapis.com", priority=1),
            ServiceEndpoint("openai", "https://api.openai.com", priority=2),
        ])
        
        self.register_service("vision", [
            ServiceEndpoint("gemini_vision", "https://generativelanguage.googleapis.com", priority=1),
            ServiceEndpoint("azure_vision", "https://vision.azure.com", priority=2),
        ])
        
        for service_name in self.services:
            self.circuit_breakers[service_name] = CircuitBreaker(
                name=service_name,
                config=CircuitBreakerConfig()
            )
            self.retry_configs[service_name] = RetryConfig()
    
    def register_service(self, service_name: str, endpoints: List[ServiceEndpoint]):
        self.services[service_name] = sorted(endpoints, key=lambda x: x.priority)
        self.health_status[service_name] = ServiceStatus.UNKNOWN
        self._latency_history[service_name] = deque(maxlen=50)
    
    def get_active_endpoint(self, service_name: str) -> Optional[ServiceEndpoint]:
        if service_name not in self.services:
            return None
        
        endpoints = self.services[service_name]
        
        for endpoint in endpoints:
            cb = self.circuit_breakers.get(service_name)
            if cb and not cb.can_execute():
                continue
            
            status = self.health_status.get(f"{service_name}:{endpoint.name}", ServiceStatus.UNKNOWN)
            if status not in [ServiceStatus.UNHEALTHY, ServiceStatus.OFFLINE]:
                return endpoint
        
        return endpoints[0] if endpoints else None
    
    def get_fallback_chain(self, service_name: str) -> List[ServiceEndpoint]:
        if service_name not in self.services:
            return []
        
        endpoints = self.services[service_name]
        cb = self.circuit_breakers.get(service_name)
        
        if cb and cb.state == CircuitState.OPEN:
            return [e for e in endpoints if e.priority > 1]
        
        return endpoints
    
    async def execute_with_failover(
        self,
        service_name: str,
        operation: Callable[[ServiceEndpoint], Awaitable[Any]],
        fallback_operation: Optional[Callable[[ServiceEndpoint], Awaitable[Any]]] = None
    ) -> Any:
        start_time = time.time()
        endpoints = self.get_fallback_chain(service_name)
        
        last_error = None
        for endpoint in endpoints:
            cb = self.circuit_breakers.get(service_name)
            if cb and not cb.can_execute():
                continue
            
            try:
                result = await self._execute_with_retry(
                    service_name,
                    endpoint,
                    operation
                )
                
                if cb:
                    cb.record_success()
                
                latency = (time.time() - start_time) * 1000
                self._record_latency(service_name, endpoint.name, latency)
                
                self._record_event("success", service_name, {
                    "endpoint": endpoint.name,
                    "latency_ms": latency
                })
                
                return result
                
            except Exception as e:
                last_error = e
                if cb:
                    cb.record_failure()
                
                self._record_event("failure", service_name, {
                    "endpoint": endpoint.name,
                    "error": str(e)
                })
                
                self._consecutive_failures[service_name] = self._consecutive_failures.get(service_name, 0) + 1
                
                if fallback_operation:
                    try:
                        result = await fallback_operation(endpoint)
                        return result
                    except:
                        pass
        
        if fallback_operation:
            try:
                return await fallback_operation(None)
            except:
                pass
        
        raise last_error or Exception(f"All endpoints failed for {service_name}")
    
    async def _execute_with_retry(
        self,
        service_name: str,
        endpoint: ServiceEndpoint,
        operation: Callable
    ) -> Any:
        config = self.retry_configs.get(service_name, RetryConfig())
        last_error = None
        
        for attempt in range(config.max_attempts):
            try:
                start = time.time()
                result = await asyncio.wait_for(
                    operation(endpoint),
                    timeout=endpoint.timeout_ms / 1000
                )
                return result
                
            except asyncio.TimeoutError:
                last_error = Exception(f"Timeout after {endpoint.timeout_ms}ms")
            except Exception as e:
                last_error = e
            
            if attempt < config.max_attempts - 1:
                delay = self._calculate_delay(attempt, config)
                await asyncio.sleep(delay / 1000)
        
        raise last_error or Exception("Max retries exceeded")
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        delay = config.base_delay_ms * (config.exponential_base ** attempt)
        delay = min(delay, config.max_delay_ms)
        
        if config.jitter:
            jitter_range = delay * 0.2
            delay += random.uniform(-jitter_range, jitter_range)
        
        return delay
    
    async def health_check(self, service_name: str, endpoint: ServiceEndpoint) -> HealthCheckResult:
        start = time.time()
        
        try:
            await asyncio.sleep(0.01)
            
            latency = (time.time() - start) * 1000
            
            is_healthy = random.random() > 0.05
            
            if is_healthy:
                self.health_status[f"{service_name}:{endpoint.name}"] = ServiceStatus.HEALTHY
                return HealthCheckResult(
                    service_name=endpoint.name,
                    status=ServiceStatus.HEALTHY,
                    latency_ms=latency,
                    timestamp=time.time()
                )
            else:
                self.health_status[f"{service_name}:{endpoint.name}"] = ServiceStatus.DEGRADED
                return HealthCheckResult(
                    service_name=endpoint.name,
                    status=ServiceStatus.DEGRADED,
                    latency_ms=latency,
                    timestamp=time.time(),
                    error="Simulated health check failure"
                )
                
        except Exception as e:
            self.health_status[f"{service_name}:{endpoint.name}"] = ServiceStatus.UNHEALTHY
            return HealthCheckResult(
                service_name=endpoint.name,
                status=ServiceStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                timestamp=time.time(),
                error=str(e)
            )
    
    async def run_health_checks(self):
        for service_name, endpoints in self.services.items():
            all_unhealthy = True
            for endpoint in endpoints:
                result = await self.health_check(service_name, endpoint)
                if result.status == ServiceStatus.HEALTHY:
                    all_unhealthy = False
                    break
            
            if all_unhealthy:
                self.health_status[service_name] = ServiceStatus.OFFLINE
            elif any(self.health_status.get(f"{service_name}:{e.name}") == ServiceStatus.DEGRADED for e in endpoints):
                self.health_status[service_name] = ServiceStatus.DEGRADED
            else:
                self.health_status[service_name] = ServiceStatus.HEALTHY
    
    def _record_latency(self, service_name: str, endpoint_name: str, latency_ms: float):
        if service_name in self._latency_history:
            self._latency_history[service_name].append({
                "endpoint": endpoint_name,
                "latency_ms": latency_ms,
                "timestamp": time.time()
            })
    
    def _record_event(self, event_type: str, service_name: str, details: Dict):
        self._event_history.append(FailoverEvent(
            timestamp=time.time(),
            event_type=event_type,
            service_name=service_name,
            details=details
        ))
    
    def get_circuit_state(self, service_name: str) -> CircuitState:
        cb = self.circuit_breakers.get(service_name)
        return cb.state if cb else CircuitState.UNKNOWN
    
    def reset_circuit(self, service_name: str):
        if service_name in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker(
                name=service_name,
                config=CircuitBreakerConfig()
            )
    
    def get_service_health(self, service_name: str) -> Dict[str, Any]:
        endpoints = self.services.get(service_name, [])
        
        endpoint_status = []
        for ep in endpoints:
            key = f"{service_name}:{ep.name}"
            status = self.health_status.get(key, ServiceStatus.UNKNOWN)
            endpoint_status.append({
                "name": ep.name,
                "priority": ep.priority,
                "status": status.value
            })
        
        cb = self.circuit_breakers.get(service_name)
        
        return {
            "service": service_name,
            "overall_status": self.health_status.get(service_name, ServiceStatus.UNKNOWN).value,
            "circuit_state": cb.state.value if cb else "unknown",
            "endpoints": endpoint_status,
            "avg_latency_ms": self._calculate_avg_latency(service_name),
            "consecutive_failures": self._consecutive_failures.get(service_name, 0)
        }
    
    def _calculate_avg_latency(self, service_name: str) -> float:
        history = self._latency_history.get(service_name, [])
        if not history:
            return 0.0
        
        latencies = [h["latency_ms"] for h in history]
        return round(sum(latencies) / len(latencies), 2)
    
    def get_all_service_health(self) -> List[Dict[str, Any]]:
        return [self.get_service_health(name) for name in self.services.keys()]
    
    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        events = list(self._event_history)[-limit:]
        return [
            {
                "timestamp": e.timestamp,
                "type": e.event_type,
                "service": e.service_name,
                "details": e.details
            }
            for e in reversed(events)
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        total_events = len(self._event_history)
        failures = sum(1 for e in self._event_history if e.event_type == "failure")
        
        circuit_states = {
            name: cb.state.value 
            for name, cb in self.circuit_breakers.items()
        }
        
        return {
            "total_events": total_events,
            "failures": failures,
            "failure_rate": round(failures / total_events, 4) if total_events > 0 else 0,
            "circuit_states": circuit_states,
            "services_count": len(self.services),
            "healthy_services": sum(1 for s in self.health_status.values() if s == ServiceStatus.HEALTHY)
        }
    
    def set_retry_config(self, service_name: str, config: RetryConfig):
        self.retry_configs[service_name] = config
    
    def get_retry_config(self, service_name: str) -> RetryConfig:
        return self.retry_configs.get(service_name, RetryConfig())


failover_manager = FailoverManager()