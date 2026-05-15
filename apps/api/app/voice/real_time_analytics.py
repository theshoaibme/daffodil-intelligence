import time
import math
from typing import Optional, Dict, List, Any, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import random


class MetricType(Enum):
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    QUALITY = "quality"
    ENGAGEMENT = "engagement"
    SENTIMENT = "sentiment"
    PERFORMANCE = "performance"


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class TimeSeriesPoint:
    timestamp: float
    value: float
    label: str = ""


@dataclass
class WaveformData:
    samples: List[float]
    peak: float
    rms: float
    average: float
    timestamp: float


@dataclass
class EngagementMetric:
    user_active_time_ms: float
    response_time_ms: float
    interaction_count: int
    attention_score: float
    pause_frequency: float


@dataclass
class PerformanceMetric:
    component: str
    latency_ms: float
    success_rate: float
    throughput_rps: float
    error_count: int


@dataclass
class AnalyticsAlert:
    alert_id: str
    level: AlertLevel
    message: str
    timestamp: float
    metric_type: MetricType
    value: float
    threshold: float


class RealTimeAnalytics:
    def __init__(self):
        self.user_sessions: Dict[int, Dict] = {}
        self.metrics_history: Dict[str, deque] = {}
        self.alerts: deque = deque(maxlen=50)
        self.dashboards: Dict[str, Dict] = {}
        
        self.max_history_points = 200
        
        self._initialize_metrics_streams()
        
        self.alert_thresholds = {
            "latency_ms": 500,
            "error_rate": 0.05,
            "quality_score": 0.6,
            "engagement_score": 0.3
        }
        
        self.max_history_points = 200
    
    def _initialize_metrics_streams(self):
        self.metrics_streams = {
            "latency": deque(maxlen=self.max_history_points),
            "throughput": deque(maxlen=self.max_history_points),
            "quality": deque(maxlen=self.max_history_points),
            "engagement": deque(maxlen=self.max_history_points),
            "sentiment": deque(maxlen=self.max_history_points),
            "audio_levels": deque(maxlen=self.max_history_points),
            "processing_time": deque(maxlen=self.max_history_points)
        }
    
    def start_session(self, user_id: int) -> Dict[str, Any]:
        self.user_sessions[user_id] = {
            "started_at": time.time(),
            "interactions": 0,
            "total_audio_duration_ms": 0,
            "sentiment_timeline": [],
            "engagement_scores": [],
            "active_time_ms": 0,
            "last_activity": time.time()
        }
        
        return {
            "session_id": f"session_{user_id}_{int(time.time() * 1000)}",
            "user_id": user_id,
            "started": True
        }
    
    def end_session(self, user_id: int) -> Dict[str, Any]:
        if user_id not in self.user_sessions:
            return {"error": "Session not found"}
        
        session = self.user_sessions[user_id]
        duration_ms = (time.time() - session["started_at"]) * 1000
        
        session_data = {
            "user_id": user_id,
            "duration_ms": duration_ms,
            "interactions": session["interactions"],
            "avg_engagement": sum(session["engagement_scores"]) / len(session["engagement_scores"]) if session["engagement_scores"] else 0,
            "sentiment_trend": self._calculate_sentiment_trend(session["sentiment_timeline"])
        }
        
        del self.user_sessions[user_id]
        
        return session_data
    
    def record_audio_level(self, user_id: int, level_db: float) -> WaveformData:
        if user_id not in self.user_sessions:
            self.start_session(user_id)
        
        samples = self._generate_waveform_samples(level_db)
        
        waveform = WaveformData(
            samples=samples,
            peak=max(abs(s) for s in samples) if samples else 0,
            rms=self._calculate_rms(samples),
            average=sum(samples) / len(samples) if samples else 0,
            timestamp=time.time()
        )
        
        self.metrics_streams["audio_levels"].append({
            "timestamp": waveform.timestamp,
            "peak": waveform.peak,
            "rms": waveform.rms,
            "level_db": level_db
        })
        
        return waveform
    
    def _generate_waveform_samples(self, level_db: float) -> List[float]:
        amplitude = 10 ** (level_db / 20)
        samples = []
        
        for i in range(32):
            noise = random.uniform(-0.1, 0.1)
            sample = amplitude * math.sin(i * 0.5) + noise * amplitude
            samples.append(round(sample, 4))
        
        return samples
    
    def _calculate_rms(self, samples: List[float]) -> float:
        if not samples:
            return 0.0
        return math.sqrt(sum(s * s for s in samples) / len(samples))
    
    def record_interaction(self, user_id: int, interaction_type: str) -> Dict[str, Any]:
        if user_id not in self.user_sessions:
            self.start_session(user_id)
        
        session = self.user_sessions[user_id]
        session["interactions"] += 1
        session["last_activity"] = time.time()
        
        return {
            "interaction_count": session["interactions"],
            "type": interaction_type,
            "timestamp": time.time()
        }
    
    def record_sentiment(self, user_id: int, sentiment: str, score: float) -> Dict[str, Any]:
        if user_id not in self.user_sessions:
            self.start_session(user_id)
        
        session = self.user_sessions[user_id]
        
        entry = {
            "sentiment": sentiment,
            "score": score,
            "timestamp": time.time()
        }
        
        session["sentiment_timeline"].append(entry)
        
        self.metrics_streams["sentiment"].append({
            "timestamp": entry["timestamp"],
            "sentiment": sentiment,
            "score": score
        })
        
        return entry
    
    def _calculate_sentiment_trend(self, timeline: List[Dict]) -> str:
        if not timeline:
            return "neutral"
        
        recent = timeline[-5:]
        scores = [t["score"] for t in recent]
        avg = sum(scores) / len(scores)
        
        if avg > 0.6:
            return "positive"
        elif avg < 0.4:
            return "negative"
        return "neutral"
    
    def calculate_engagement(self, user_id: int) -> EngagementMetric:
        if user_id not in self.user_sessions:
            return EngagementMetric(
                user_active_time_ms=0,
                response_time_ms=0,
                interaction_count=0,
                attention_score=0,
                pause_frequency=0
            )
        
        session = self.user_sessions[user_id]
        
        active_time = (time.time() - session["started_at"]) * 1000
        interactions = session["interactions"]
        
        attention = min(1.0, interactions / 10) if interactions > 0 else 0.5
        
        engagement = EngagementMetric(
            user_active_time_ms=active_time,
            response_time_ms=200,
            interaction_count=interactions,
            attention_score=attention,
            pause_frequency=random.uniform(0, 2)
        )
        
        session["engagement_scores"].append(attention)
        
        self.metrics_streams["engagement"].append({
            "timestamp": time.time(),
            "score": attention,
            "active_time_ms": active_time
        })
        
        return engagement
    
    def record_latency(self, component: str, latency_ms: float):
        self.metrics_streams["latency"].append({
            "timestamp": time.time(),
            "component": component,
            "latency_ms": latency_ms
        })
        
        if latency_ms > self.alert_thresholds["latency_ms"]:
            self._create_alert(
                AlertLevel.WARNING,
                f"High latency in {component}: {latency_ms:.1f}ms",
                MetricType.LATENCY,
                latency_ms,
                self.alert_thresholds["latency_ms"]
            )
    
    def record_throughput(self, rps: float):
        self.metrics_streams["throughput"].append({
            "timestamp": time.time(),
            "rps": rps
        })
    
    def record_quality_score(self, score: float):
        self.metrics_streams["quality"].append({
            "timestamp": time.time(),
            "score": score
        })
        
        if score < self.alert_thresholds["quality_score"]:
            self._create_alert(
                AlertLevel.WARNING,
                f"Quality score dropped to {score:.2f}",
                MetricType.QUALITY,
                score,
                self.alert_thresholds["quality_score"]
            )
    
    def _create_alert(
        self,
        level: AlertLevel,
        message: str,
        metric_type: MetricType,
        value: float,
        threshold: float
    ):
        alert = AnalyticsAlert(
            alert_id=f"alert_{int(time.time() * 1000)}",
            level=level,
            message=message,
            timestamp=time.time(),
            metric_type=metric_type,
            value=value,
            threshold=threshold
        )
        self.alerts.append(alert)
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        return [
            {
                "id": a.alert_id,
                "level": a.level.value,
                "message": a.message,
                "timestamp": a.timestamp,
                "metric": a.metric_type.value,
                "value": round(a.value, 2),
                "threshold": a.threshold
            }
            for a in list(self.alerts)[-limit:]
        ]
    
    def get_time_series_data(
        self,
        metric_name: str,
        start_time: float = None,
        end_time: float = None
    ) -> List[TimeSeriesPoint]:
        if metric_name not in self.metrics_streams:
            return []
        
        data = self.metrics_streams[metric_name]
        
        if start_time is None and end_time is None:
            return [
                TimeSeriesPoint(
                    timestamp=d["timestamp"],
                    value=d.get("value", d.get("latency_ms", d.get("score", 0))),
                    label=metric_name
                )
                for d in data
            ]
        
        return [
            TimeSeriesPoint(
                timestamp=d["timestamp"],
                value=d.get("value", d.get("latency_ms", d.get("score", 0))),
                label=metric_name
            )
            for d in data
            if (start_time is None or d["timestamp"] >= start_time) and
               (end_time is None or d["timestamp"] <= end_time)
        ]
    
    def get_dashboard_data(self, user_id: int = None) -> Dict[str, Any]:
        latency_data = self.metrics_streams["latency"]
        quality_data = self.metrics_streams["quality"]
        engagement_data = self.metrics_streams["engagement"]
        sentiment_data = self.metrics_streams["sentiment"]
        audio_data = self.metrics_streams["audio_levels"]
        
        avg_latency = sum(d["latency_ms"] for d in latency_data) / len(latency_data) if latency_data else 0
        avg_quality = sum(d["score"] for d in quality_data) / len(quality_data) if quality_data else 0
        avg_engagement = sum(d["score"] for d in engagement_data) / len(engagement_data) if engagement_data else 0
        
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        for d in sentiment_data:
            sentiment_counts[d["sentiment"]] = sentiment_counts.get(d["sentiment"], 0) + 1
        
        audio_peaks = [d["peak"] for d in audio_data]
        avg_audio_level = sum(audio_peaks) / len(audio_peaks) if audio_peaks else 0
        
        return {
            "timestamp": time.time(),
            "metrics": {
                "latency": {
                    "current": latency_data[-1]["latency_ms"] if latency_data else 0,
                    "average": round(avg_latency, 2),
                    "max": max((d["latency_ms"] for d in latency_data), default=0),
                    "min": min((d["latency_ms"] for d in latency_data), default=0)
                },
                "quality": {
                    "current": quality_data[-1]["score"] if quality_data else 0,
                    "average": round(avg_quality, 3),
                    "trend": "improving" if avg_quality > 0.7 else "stable" if avg_quality > 0.5 else "declining"
                },
                "engagement": {
                    "current": engagement_data[-1]["score"] if engagement_data else 0,
                    "average": round(avg_engagement, 3),
                    "sessions_active": len(self.user_sessions)
                },
                "audio": {
                    "peak": audio_peaks[-1] if audio_peaks else 0,
                    "average": round(avg_audio_level, 3),
                    "level_db": audio_data[-1]["level_db"] if audio_data else -40
                },
                "sentiment": sentiment_counts,
                "alerts": {
                    "count": len(self.alerts),
                    "recent": len([a for a in self.alerts if time.time() - a.timestamp < 60])
                }
            },
            "summary": {
                "health_score": min(1.0, (avg_quality + avg_engagement) / 2),
                "status": "healthy" if avg_latency < 300 and avg_quality > 0.6 else "degraded",
                "recommendations": self._generate_recommendations(avg_latency, avg_quality, avg_engagement)
            }
        }
    
    def _generate_recommendations(
        self,
        avg_latency: float,
        avg_quality: float,
        avg_engagement: float
    ) -> List[str]:
        recommendations = []
        
        if avg_latency > 400:
            recommendations.append("Consider optimizing response time for better user experience")
        
        if avg_quality < 0.6:
            recommendations.append("Audio quality could be improved - check microphone settings")
        
        if avg_engagement < 0.4:
            recommendations.append("User engagement is low - consider more interactive elements")
        
        if not recommendations:
            recommendations.append("System performing well - all metrics within acceptable ranges")
        
        return recommendations
    
    def get_live_chart_data(self, metric_name: str, points: int = 50) -> Dict[str, Any]:
        data = list(self.metrics_streams.get(metric_name, []))[-points:]
        
        labels = [d["timestamp"] for d in data]
        values = []
        
        for d in data:
            if metric_name == "latency":
                values.append(d.get("latency_ms", 0))
            elif metric_name == "quality":
                values.append(d.get("score", 0))
            elif metric_name == "engagement":
                values.append(d.get("score", 0))
            elif metric_name == "audio_levels":
                values.append(d.get("rms", 0))
            else:
                values.append(d.get("value", 0))
        
        return {
            "metric": metric_name,
            "labels": labels,
            "data": values,
            "count": len(values)
        }
    
    def stream_analytics(self, user_id: int = None) -> AsyncGenerator[Dict, None]:
        while True:
            dashboard = self.get_dashboard_data(user_id)
            yield dashboard
            import asyncio
            asyncio.sleep(1)
    
    def get_performance_breakdown(self) -> List[PerformanceMetric]:
        components = ["stt", "llm", "tts", "translation", "video"]
        
        return [
            PerformanceMetric(
                component=comp,
                latency_ms=50 + random.uniform(0, 100),
                success_rate=0.95 + random.uniform(0, 0.05),
                throughput_rps=10 + random.uniform(0, 20),
                error_count=random.randint(0, 5)
            )
            for comp in components
        ]
    
    def get_session_summary(self, user_id: int) -> Optional[Dict]:
        if user_id not in self.user_sessions:
            return None
        
        session = self.user_sessions[user_id]
        
        return {
            "user_id": user_id,
            "duration_sec": round(time.time() - session["started_at"], 1),
            "interactions": session["interactions"],
            "engagement_avg": round(sum(session["engagement_scores"]) / len(session["engagement_scores"]), 3) if session["engagement_scores"] else 0,
            "sentiment_trend": self._calculate_sentiment_trend(session["sentiment_timeline"]),
            "last_activity": session["last_activity"]
        }
    
    def reset_metrics(self):
        self._initialize_metrics_streams()
        self.alerts.clear()
    
    def export_metrics(self, format: str = "json") -> Dict:
        return {
            "export_time": time.time(),
            "metrics": {
                name: list(data) 
                for name, data in self.metrics_streams.items()
            },
            "alerts": list(self.alerts),
            "active_sessions": len(self.user_sessions)
        }


real_time_analytics = RealTimeAnalytics()