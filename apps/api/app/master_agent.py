import asyncio
import time
import uuid
import threading
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


try:
    import orjson
    def json_dumps(obj): return orjson.dumps(obj)
    def json_loads(data): return orjson.loads(data)
except ImportError:
    import json
    def json_dumps(obj): return json.dumps(obj).encode()
    def json_loads(data): return json.loads(data.decode() if isinstance(data, bytes) else data)


try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class TaskPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class TaskContext:
    task_id: str
    session_id: str
    task_type: str
    name: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict] = None
    error: Optional[str] = None


class AsyncSemaphore:
    def __init__(self, value: int):
        self._value = value
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        async with self._lock:
            while self._value <= 0:
                await asyncio.sleep(0.01)
            self._value -= 1
    
    def release(self):
        self._value += 1


class MemoryManager:
    def __init__(self, use_redis: bool = True):
        self._lock = asyncio.Lock()
        self._redis_available = False
        
        self._conversation: Dict[str, List] = defaultdict(list)
        self._episodes: List[Dict] = []
        self._entities: Dict[str, Any] = {}
        self._working: Dict[str, Any] = {}
    
    async def add_conversation(self, session_id: str, role: str, content: str, metadata: Dict = None):
        entry = {
            "id": str(uuid.uuid4())[:8],
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        async with self._lock:
            self._conversation[session_id].append(entry)
            if len(self._conversation[session_id]) > 50:
                self._conversation[session_id] = self._conversation[session_id][-50:]

        # Bridge to the unified MemoryService so user turns also land in the
        # shared long-term semantic store (best-effort, never blocks the path).
        if role == "user" and content:
            try:
                from .memory import memory_service
                await memory_service.remember(
                    content,
                    user_id=(metadata or {}).get("user_id", session_id),
                    metadata={"session_id": session_id, "source": "master_agent"},
                )
            except Exception:
                pass
        return entry["id"]
    
    async def get_conversation(self, session_id: str, turns: int = 10) -> List[Dict]:
        async with self._lock:
            return self._conversation.get(session_id, [])[-turns:]
    
    async def store_episode(self, session_id: str, data: Dict):
        episode = {"id": str(uuid.uuid4())[:8], "session_id": session_id, **data, "timestamp": time.time()}
        async with self._lock:
            self._episodes.append(episode)
            if len(self._episodes) > 100:
                self._episodes = self._episodes[-100:]
        return episode["id"]
    
    async def search_episodes(self, query: str, limit: int = 5) -> List[Dict]:
        async with self._lock:
            results = []
            for ep in reversed(self._episodes):
                if query.lower() in ep.get("prompt", "").lower():
                    results.append(ep)
                    if len(results) >= limit:
                        break
            return results
    
    async def cache_entity(self, entity_type: str, entity_id: str, data: Dict):
        key = f"{entity_type}:{entity_id}"
        async with self._lock:
            self._entities[key] = data
    
    async def get_entity(self, entity_type: str, entity_id: str) -> Optional[Dict]:
        key = f"{entity_type}:{entity_id}"
        async with self._lock:
            return self._entities.get(key)
    
    async def store_working(self, key: str, value: Any, ttl: int = 300):
        async with self._lock:
            self._working[key] = {"value": value, "expiry": time.time() + ttl}
    
    async def get_working(self, key: str) -> Optional[Any]:
        async with self._lock:
            item = self._working.get(key)
            if item and time.time() > item["expiry"]:
                del self._working[key]
                return None
            return item["value"] if item else None
    
    async def clear_conversation(self, session_id: str):
        async with self._lock:
            self._conversation.pop(session_id, None)
    
    async def get_stats(self) -> Dict:
        async with self._lock:
            return {
                "connected": self._redis_available,
                "storage_type": "redis" if self._redis_available else "memory",
                "active_conversations": len(self._conversation),
                "episodes_stored": len(self._episodes),
                "entities_cached": len(self._entities)
            }


class ParallelTaskRunner:
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._semaphore = AsyncSemaphore(max_concurrent)
        self._running: Dict[str, asyncio.Task] = {}
        self._results: Dict[str, asyncio.Event] = {}
        self._task_data: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
    
    async def submit(self, task_id: str, coro):
        await self._semaphore.acquire()
        
        result_event = asyncio.Event()
        async with self._lock:
            self._results[task_id] = result_event
            self._task_data[task_id] = {"status": "pending", "result": None, "error": None}
        
        async_task = asyncio.create_task(self._run_task(task_id, coro, result_event))
        
        async with self._lock:
            self._running[task_id] = async_task
        
        return task_id
    
    async def _run_task(self, task_id: str, coro, result_event: asyncio.Event):
        try:
            async with self._lock:
                self._task_data[task_id]["status"] = "running"
            
            result = await coro
            
            async with self._lock:
                self._task_data[task_id]["status"] = "completed"
                self._task_data[task_id]["result"] = result
        except Exception as e:
            async with self._lock:
                self._task_data[task_id]["status"] = "failed"
                self._task_data[task_id]["error"] = str(e)
        finally:
            self._semaphore.release()
            result_event.set()
        
        return task_id
    
    async def wait(self, task_id: str, timeout: float = 30.0) -> Optional[Any]:
        async with self._lock:
            event = self._results.get(task_id)
        
        if not event:
            return None
        
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass
        
        async with self._lock:
            data = self._task_data.get(task_id, {})
        
        if data.get("error"):
            raise Exception(data["error"])
        return data.get("result")
    
    async def get_status(self, task_id: str) -> Dict:
        async with self._lock:
            return self._task_data.get(task_id, {"status": "unknown"})
    
    def get_running_count(self) -> int:
        return len(self._running)


class MasterAgent:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._sessions: Dict[str, Dict] = {}
        self._memory = MemoryManager()
        self._task_runner = ParallelTaskRunner(max_concurrent=20)
        
        self.agents = {
            "coordinator": {"name": "Coordinator Agent", "capabilities": ["route", "coordinate", "aggregate", "plan"], "color": "#3B82F6", "icon": "🔄"},
            "research": {"name": "Research Agent", "capabilities": ["search", "lookup", "fetch", "scrape"], "color": "#10B981", "icon": "🔍"},
            "analysis": {"name": "Analysis Agent", "capabilities": ["analyze", "evaluate", "compare", "assess"], "color": "#F59E0B", "icon": "📊"},
            "execution": {"name": "Execution Agent", "capabilities": ["execute", "run", "perform", "code"], "color": "#EF4444", "icon": "⚡"},
            "communication": {"name": "Communication Agent", "capabilities": ["respond", "explain", "summarize"], "color": "#8B5CF6", "icon": "💬"},
            "routine": {"name": "Routine Agent", "capabilities": ["schedule", "automate", "remind", "routine", "daily", "weekly", "monthly"], "color": "#06B6D4", "icon": "⏰"},
            "google_search": {"name": "Google Search Agent", "capabilities": ["search web", "google", "web search", "online search", "internet"], "color": "#4285F4", "icon": "🔎"}
        }
        
        self.tools = {
            "get_cgpa": {"name": "Get CGPA", "category": "academic", "color": "#06B6D4", "icon": "📈"},
            "get_courses": {"name": "Get Courses", "category": "academic", "color": "#06B6D4", "icon": "📚"},
            "search_books": {"name": "Search Books", "category": "library", "color": "#84CC16", "icon": "📖"},
            "get_jobs": {"name": "Search Jobs", "category": "career", "color": "#EC4899", "icon": "💼"},
            "get_shuttle_schedule": {"name": "Get Shuttle Schedule", "category": "transport", "color": "#A855F7", "icon": "🚌"},
        }
        
        self.intents = {
            "research": ["search", "find", "lookup", "research", "what is", "who is"],
            "analysis": ["analyze", "compare", "evaluate", "assess", "review", "examine"],
            "academic": ["cgpa", "gpa", "grade", "course", "semester", "exam", "result"],
            "career": ["job", "jobs", "career", "internship", "cv", "resume"],
            "library": ["book", "books", "library", "reference"],
            "financial": ["fee", "tuition", "scholarship", "payment"],
            "transport": ["shuttle", "bus", "transport", "route"],
            "routine": ["schedule", "remind", "routine", "daily", "weekly", "monthly", "alarm", "calendar"],
            "google_search": ["search web", "google", "web search", "online", "internet", "browse", "look up online"]
        }
    
    def _detect_intent(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        for intent, patterns in self.intents.items():
            if any(p in prompt_lower for p in patterns):
                return intent
        return "general"
    
    def _detect_agents(self, prompt: str) -> List[str]:
        prompt_lower = prompt.lower()
        agents = set()
        
        for intent, patterns in self.intents.items():
            if any(p in prompt_lower for p in patterns):
                if intent in self.agents:
                    if intent in ["research", "analysis", "execution", "communication", "routine", "google_search"]:
                        agents.add(intent)
        
        if not agents:
            agents.add("coordinator")
        
        return list(agents)
    
    def _detect_tools(self, prompt: str) -> List[str]:
        prompt_lower = prompt.lower()
        tools = []
        
        tool_keywords = {
            "get_cgpa": ["cgpa", "gpa", "grade", "grades", "performance"],
            "get_courses": ["course", "courses", "subject", "classes"],
            "search_books": ["book", "books", "library"],
            "get_jobs": ["job", "jobs", "career", "internship"],
            "get_shuttle_schedule": ["shuttle", "bus", "transport", "schedule"],
        }
        
        for tool_name, keywords in tool_keywords.items():
            if any(kw in prompt_lower for kw in keywords):
                if tool_name not in tools:
                    tools.append(tool_name)
        
        return tools

    def _resolve_user_context(self, user_id: int) -> Dict[str, Any]:
        """Load registered profile fields (e.g. student_id) for tool arg inference."""
        ctx: Dict[str, Any] = {"user_id": user_id}
        if not user_id:
            return ctx
        try:
            from .integrations.telegram.auth_store import auth_store
            acct = auth_store.get_by_telegram_id(int(user_id))
            if acct:
                if acct.student_id:
                    ctx["student_id"] = acct.student_id
                ctx["email"] = acct.email
                ctx["role"] = acct.role
                if acct.department:
                    ctx["department"] = acct.department
        except Exception:
            pass
        return ctx
    
    async def process(self, prompt: str, user_id: int = 0, session_id: str = None, priority: TaskPriority = TaskPriority.NORMAL) -> str:
        if not session_id:
            session_id = str(uuid.uuid4())[:8]
        
        await self._memory.add_conversation(session_id, "user", prompt, {"user_id": user_id})
        
        intent = self._detect_intent(prompt)
        agents = self._detect_agents(prompt)
        tools = self._detect_tools(prompt)
        user_ctx = self._resolve_user_context(user_id)

        session = {
            "session_id": session_id,
            "prompt": prompt,
            "intent": intent,
            "agents": [{"type": a, **self.agents[a]} for a in agents],
            "tools": [{"name": t, **self.tools[t]} for t in tools],
            "user_id": user_id,
            "student_id": user_ctx.get("student_id"),
            "email": user_ctx.get("email"),
            "role": user_ctx.get("role"),
            "department": user_ctx.get("department"),
            "priority": priority.value,
            "created_at": time.time(),
            "status": "running",
            "tasks": []
        }
        
        async with self._lock:
            self._sessions[session_id] = session
        
        for agent_type in agents:
            task_id = f"{session_id}_{agent_type}_{int(time.time()*1000000)}"
            task = TaskContext(task_id=task_id, session_id=session_id, task_type="agent", name=self.agents[agent_type]["name"], priority=priority)
            session["tasks"].append(task)
            await self._task_runner.submit(task_id, self._execute_agent(task, prompt))
        
        for tool_name in tools:
            task_id = f"{session_id}_{tool_name}_{int(time.time()*1000000)}"
            task = TaskContext(
                task_id=task_id,
                session_id=session_id,
                task_type="tool",
                name=tool_name,
                priority=priority,
            )
            session["tasks"].append(task)
            await self._task_runner.submit(task_id, self._execute_tool(task, prompt))
        
        asyncio.create_task(self._monitor_session(session_id))
        
        return session_id
    
    async def _execute_agent(self, task: TaskContext, prompt: str):
        task.status = "running"
        task.started_at = time.time()

        try:
            # Delegate to the unified runtime so the response is REAL (Antigravity
            # main agent with tools, or legacy supervisor fallback).
            from .runtime import orchestrator
            session = self._sessions.get(task.session_id, {})
            real_user_id = session.get("user_id", 0)
            result = await orchestrator.run(
                prompt, user_id=real_user_id, chat_id=task.session_id
            )
            response_text = result.get("content", "")

            task.result = {
                "task_id": task.task_id,
                "type": "agent",
                "agent_name": task.name,
                "status": "completed",
                "intent_detected": self._detect_intent(prompt),
                "response": response_text,
                "tools_used": result.get("tool_calls", []),
                "engine": result.get("engine"),
                "timestamp": time.time(),
                "duration_ms": round((time.time() - task.started_at) * 1000, 2),
            }
            task.status = "completed"

            # Surface a session-level response for callers that read it.
            session = self._sessions.get(task.session_id)
            if session is not None and response_text and not session.get("response"):
                session["response"] = response_text
        except Exception as e:
            task.status = "failed"
            task.error = str(e)

        task.completed_at = time.time()
        return task.task_id

    async def _execute_tool(self, task: TaskContext, prompt: str):
        task.status = "running"
        task.started_at = time.time()

        try:
            from .tools.registry import get_registry
            from .tools.arg_inference import infer_tool_kwargs, missing_required

            registry = get_registry()
            tool = registry.get(task.name)

            if tool is not None:
                session = self._sessions.get(task.session_id, {})
                context = {
                    "student_id": session.get("student_id"),
                    "user_id": session.get("user_id"),
                }
                kwargs = infer_tool_kwargs(tool, prompt, context)
                missing = missing_required(tool, kwargs)
                if missing:
                    task.result = {
                        "task_id": task.task_id,
                        "type": "tool",
                        "tool_name": tool.name,
                        "category": tool.category,
                        "status": "failed",
                        "error": f"Missing required arguments: {', '.join(missing)}",
                        "inferred_args": kwargs,
                        "timestamp": time.time(),
                        "duration_ms": round((time.time() - task.started_at) * 1000, 2),
                    }
                else:
                    exec_result = await registry.execute(tool.name, **kwargs)
                    task.result = {
                        "task_id": task.task_id,
                        "type": "tool",
                        "tool_name": tool.name,
                        "category": tool.category,
                        "status": "executed" if exec_result.success else "failed",
                        "args": kwargs,
                        "data": exec_result.data,
                        "error": exec_result.error,
                        "timestamp": time.time(),
                        "duration_ms": exec_result.duration_ms,
                    }
            else:
                meta = self.tools.get(task.name, {})
                task.result = {
                    "task_id": task.task_id,
                    "type": "tool",
                    "tool_name": task.name,
                    "category": meta.get("category", "general"),
                    "status": "skipped",
                    "note": "No matching registry tool",
                    "timestamp": time.time(),
                    "duration_ms": round((time.time() - task.started_at) * 1000, 2),
                }
            task.status = "completed"
        except Exception as e:
            task.status = "failed"
            task.error = str(e)

        task.completed_at = time.time()
        return task.task_id
    
    async def _monitor_session(self, session_id: str):
        max_wait = 30
        start = time.time()
        
        while time.time() - start < max_wait:
            all_done = True
            
            async with self._lock:
                session = self._sessions.get(session_id)
                if session:
                    for task in session["tasks"]:
                        status = await self._task_runner.get_status(task.task_id)
                        if status.get("status") not in ["completed", "failed"]:
                            all_done = False
                            break
                    
                    if all_done:
                        session["status"] = "completed"
                        for task in session["tasks"]:
                            status = await self._task_runner.get_status(task.task_id)
                            task.result = status.get("result")
                            task.status = status.get("status", "unknown")
                            if status.get("error"):
                                task.error = status.get("error")
                        
                        await self._memory.store_episode(session_id, {
                            "prompt": session["prompt"],
                            "intent": session["intent"],
                            "tasks_count": len(session["tasks"]),
                            "status": "completed"
                        })
                        return
            
            await asyncio.sleep(0.1)
        
        async with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["status"] = "timeout"
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        async with self._lock:
            session = self._sessions.get(session_id)
        
        if not session:
            return None
        
        task_states = []
        for task in session["tasks"]:
            status_data = await self._task_runner.get_status(task.task_id)
            
            duration = 0
            if task.started_at:
                end = task.completed_at or time.time()
                duration = round((end - task.started_at) * 1000, 1)
            
            task_states.append({
                "task_id": task.task_id,
                "name": task.name,
                "type": task.task_type,
                "status": status_data.get("status", task.status),
                "duration_ms": duration,
                "result": task.result,
                "error": task.error
            })
        
        conversation = await self._memory.get_conversation(session_id, turns=5)
        
        return {
            "session_id": session_id,
            "user_id": session.get("user_id"),
            "prompt": session["prompt"],
            "intent": session["intent"],
            "status": session["status"],
            "created_at": session["created_at"],
            "agents_used": [a["name"] for a in session["agents"]],
            "tools_used": [t["name"] for t in session["tools"]],
            "total_tasks": len(task_states),
            "completed_tasks": sum(1 for t in task_states if t["status"] == "completed"),
            "failed_tasks": sum(1 for t in task_states if t["status"] == "failed"),
            "tasks": task_states,
            "conversation_context": [c["content"] for c in conversation],
            "memory_stats": await self._memory.get_stats()
        }
    
    async def get_all_sessions(self) -> List[Dict]:
        return [await self.get_session(sid) for sid in list(self._sessions.keys())]
    
    async def get_active_sessions(self) -> List[Dict]:
        return [await self.get_session(sid) for sid in list(self._sessions.keys()) if self._sessions[sid]["status"] == "running"]
    
    async def get_stats(self) -> Dict:
        total = len(self._sessions)
        running = sum(1 for s in self._sessions.values() if s["status"] == "running")
        completed = sum(1 for s in self._sessions.values() if s["status"] == "completed")
        
        total_tasks = sum(len(s["tasks"]) for s in self._sessions.values())
        total_agents = sum(len(s["agents"]) for s in self._sessions.values())
        total_tools = sum(len(s["tools"]) for s in self._sessions.values())
        
        return {
            "total_sessions": total,
            "running": running,
            "completed": completed,
            "total_tasks_executed": total_tasks,
            "total_agents_called": total_agents,
            "total_tools_called": total_tools,
            "concurrent_capacity": self._task_runner.max_concurrent,
            "currently_running": self._task_runner.get_running_count(),
            "available_agents": len(self.agents),
            "available_tools": len(self.tools),
            "memory": await self._memory.get_stats()
        }
    
    async def clear_session(self, session_id: str):
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
        await self._memory.clear_conversation(session_id)


master_agent = MasterAgent()