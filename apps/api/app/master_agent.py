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
            "check_prerequisites": {"name": "Check Prerequisites", "category": "academic", "color": "#06B6D4", "icon": "✅"},
            "search_books": {"name": "Search Books", "category": "library", "color": "#84CC16", "icon": "📖"},
            "get_notices": {"name": "Get Notices", "category": "admin", "color": "#F97316", "icon": "📢"},
            "search_jobs": {"name": "Search Jobs", "category": "career", "color": "#EC4899", "icon": "💼"},
            "analyze_cv": {"name": "Analyze CV", "category": "career", "color": "#EC4899", "icon": "📋"},
            "calculate_tuition": {"name": "Calculate Tuition", "category": "financial", "color": "#14B8A6", "icon": "💰"},
            "get_scholarships": {"name": "Get Scholarships", "category": "financial", "color": "#14B8A6", "icon": "🎓"},
            "get_shuttle_schedule": {"name": "Get Shuttle Schedule", "category": "transport", "color": "#A855F7", "icon": "🚌"}
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
            "check_prerequisites": ["prerequisite", "required course"],
            "search_books": ["book", "books", "library"],
            "get_notices": ["notice", "notices", "announcement"],
            "search_jobs": ["job", "jobs", "career", "internship"],
            "analyze_cv": ["cv", "resume", "check my cv"],
            "calculate_tuition": ["tuition", "fee", "fees", "payment"],
            "get_scholarships": ["scholarship", "scholarships", "financial aid"],
            "get_shuttle_schedule": ["shuttle", "bus", "transport", "schedule"]
        }
        
        for tool_name, keywords in tool_keywords.items():
            if any(kw in prompt_lower for kw in keywords):
                if tool_name not in tools:
                    tools.append(tool_name)
        
        return tools
    
    async def process(self, prompt: str, user_id: int = 0, session_id: str = None, priority: TaskPriority = TaskPriority.NORMAL) -> str:
        if not session_id:
            session_id = str(uuid.uuid4())[:8]
        
        await self._memory.add_conversation(session_id, "user", prompt, {"user_id": user_id})
        
        intent = self._detect_intent(prompt)
        agents = self._detect_agents(prompt)
        tools = self._detect_tools(prompt)
        
        session = {
            "session_id": session_id,
            "prompt": prompt,
            "intent": intent,
            "agents": [{"type": a, **self.agents[a]} for a in agents],
            "tools": [{"name": t, **self.tools[t]} for t in tools],
            "user_id": user_id,
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
            task = TaskContext(task_id=task_id, session_id=session_id, task_type="tool", name=self.tools[tool_name]["name"], priority=priority)
            session["tasks"].append(task)
            await self._task_runner.submit(task_id, self._execute_tool(task, prompt))
        
        asyncio.create_task(self._monitor_session(session_id))
        
        return session_id
    
    async def _execute_agent(self, task: TaskContext, prompt: str):
        task.status = "running"
        task.started_at = time.time()
        
        try:
            await asyncio.sleep(0.05)
            
            task.result = {
                "task_id": task.task_id,
                "type": "agent",
                "agent_name": task.name,
                "status": "completed",
                "intent_detected": self._detect_intent(prompt),
                "timestamp": time.time(),
                "duration_ms": 50
            }
            task.status = "completed"
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
        
        task.completed_at = time.time()
        return task.task_id
    
    async def _execute_tool(self, task: TaskContext, prompt: str):
        task.status = "running"
        task.started_at = time.time()
        
        try:
            await asyncio.sleep(0.03)
            
            task.result = {
                "task_id": task.task_id,
                "type": "tool",
                "tool_name": task.name,
                "category": "general",
                "status": "executed",
                "timestamp": time.time(),
                "duration_ms": 30
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