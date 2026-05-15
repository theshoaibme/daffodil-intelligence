import asyncio
import time
from typing import Optional, Dict, List, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import json


class AgentType(Enum):
    COORDINATOR = "coordinator"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    EXECUTION = "execution"
    COMMUNICATION = "communication"
    MONITORING = "monitoring"
    SPECIALIST = "specialist"


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class AgentCapability:
    name: str
    description: str
    supported_tasks: List[str]
    max_concurrent: int = 1


@dataclass
class Agent:
    agent_id: str
    agent_type: AgentType
    name: str
    capabilities: List[AgentCapability]
    status: str = "idle"
    current_tasks: List[str] = field(default_factory=list)
    completed_tasks: int = 0
    success_rate: float = 1.0
    avg_response_time_ms: float = 0.0


@dataclass
class Task:
    task_id: str
    name: str
    description: str
    required_capabilities: List[str]
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    assigned_agent: Optional[str] = None
    input_data: Dict = field(default_factory=dict)
    output_data: Optional[Dict] = None
    error: Optional[str] = None
    subtasks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class WorkflowStep:
    step_id: str
    name: str
    agent_type: AgentType
    task_template: str
    required: bool = True
    parallel: bool = False
    timeout_seconds: float = 30.0
    retry_on_failure: bool = True
    max_retries: int = 2


@dataclass
class Workflow:
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    input_schema: Dict = field(default_factory=dict)
    output_schema: Dict = field(default_factory=dict)


@dataclass
class OrchestrationResult:
    workflow_id: str
    status: str
    tasks_completed: int
    total_tasks: int
    duration_ms: float
    results: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


class AgentRegistry:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        self.register_agent(Agent(
            agent_id="coordinator_1",
            agent_type=AgentType.COORDINATOR,
            name="Main Coordinator",
            capabilities=[
                AgentCapability(
                    name="orchestration",
                    description="Coordinates other agents",
                    supported_tasks=["coordinate", "route", "aggregate"]
                )
            ]
        ))
        
        self.register_agent(Agent(
            agent_id="research_1",
            agent_type=AgentType.RESEARCH,
            name="Research Agent",
            capabilities=[
                AgentCapability(
                    name="information_retrieval",
                    description="Searches and retrieves information",
                    supported_tasks=["search", "lookup", "fetch"]
                ),
                AgentCapability(
                    name="web_scraping",
                    description="Extracts data from web sources",
                    supported_tasks=["scrape", "extract"]
                )
            ]
        ))
        
        self.register_agent(Agent(
            agent_id="analysis_1",
            agent_type=AgentType.ANALYSIS,
            name="Analysis Agent",
            capabilities=[
                AgentCapability(
                    name="data_analysis",
                    description="Analyzes data and patterns",
                    supported_tasks=["analyze", "evaluate", "compare"]
                ),
                AgentCapability(
                    name="sentiment_analysis",
                    description="Analyzes sentiment and emotions",
                    supported_tasks=["sentiment", "emotion"]
                )
            ]
        ))
        
        self.register_agent(Agent(
            agent_id="execution_1",
            agent_type=AgentType.EXECUTION,
            name="Execution Agent",
            capabilities=[
                AgentCapability(
                    name="task_execution",
                    description="Executes tasks and actions",
                    supported_tasks=["execute", "run", "perform"]
                ),
                AgentCapability(
                    name="code_generation",
                    description="Generates and writes code",
                    supported_tasks=["code", "generate", "implement"]
                )
            ]
        ))
    
    def register_agent(self, agent: Agent):
        self.agents[agent.agent_id] = agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.agents.get(agent_id)
    
    def find_agents_by_capability(self, capability: str) -> List[Agent]:
        matching = []
        for agent in self.agents.values():
            for cap in agent.capabilities:
                if capability in cap.supported_tasks:
                    matching.append(agent)
        return matching
    
    def find_available_agent(self, required_capabilities: List[str]) -> Optional[Agent]:
        for capability in required_capabilities:
            agents = self.find_agents_by_capability(capability)
            for agent in agents:
                if len(agent.current_tasks) < max(c.max_concurrent for c in agent.capabilities):
                    return agent
        return None
    
    def get_all_agents(self) -> List[Dict]:
        return [
            {
                "id": a.agent_id,
                "type": a.agent_type.value,
                "name": a.name,
                "status": a.status,
                "current_tasks": len(a.current_tasks),
                "completed_tasks": a.completed_tasks,
                "success_rate": round(a.success_rate, 2)
            }
            for a in self.agents.values()
        ]


class TaskQueue:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.pending_queue: deque = deque()
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.failed_tasks: Dict[str, Task] = {}
    
    def add_task(self, task: Task):
        self.tasks[task.task_id] = task
        self.pending_queue.append(task.task_id)
        self._sort_pending_queue()
    
    def _sort_pending_queue(self):
        sorted_ids = sorted(
            [tid for tid in self.pending_queue],
            key=lambda tid: self.tasks[tid].priority.value,
            reverse=True
        )
        self.pending_queue = deque(sorted_ids)
    
    def get_next_task(self) -> Optional[Task]:
        if not self.pending_queue:
            return None
        
        task_id = self.pending_queue.popleft()
        task = self.tasks.get(task_id)
        
        if task:
            self.running_tasks[task_id] = task
            task.status = TaskStatus.RUNNING
            task.started_at = time.time()
        
        return task
    
    def complete_task(self, task_id: str, output: Dict):
        if task_id in self.running_tasks:
            task = self.running_tasks.pop(task_id)
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            task.output_data = output
            self.completed_tasks[task_id] = task
    
    def fail_task(self, task_id: str, error: str):
        if task_id in self.running_tasks:
            task = self.running_tasks.pop(task_id)
            task.status = TaskStatus.FAILED
            task.completed_at = time.time()
            task.error = error
            self.failed_tasks[task_id] = task
    
    def cancel_task(self, task_id: str):
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.CANCELLED
            task.completed_at = time.time()
    
    def get_pending_count(self) -> int:
        return len(self.pending_queue)
    
    def get_running_count(self) -> int:
        return len(self.running_tasks)


class AgentOrchestrator:
    def __init__(self):
        self.registry = AgentRegistry()
        self.task_queue = TaskQueue()
        self.workflows: Dict[str, Workflow] = {}
        self.active_workflows: Dict[str, Dict] = {}
        self._execution_history: deque = deque(maxlen=100)
        
        self._initialize_default_workflows()
    
    def _initialize_default_workflows(self):
        research_workflow = Workflow(
            workflow_id="research_flow",
            name="Research Workflow",
            description="Research and analyze information",
            steps=[
                WorkflowStep(
                    step_id="step_1",
                    name="Search Information",
                    agent_type=AgentType.RESEARCH,
                    task_template="Search for {query}",
                    required=True
                ),
                WorkflowStep(
                    step_id="step_2",
                    name="Analyze Results",
                    agent_type=AgentType.ANALYSIS,
                    task_template="Analyze {data}",
                    required=True
                ),
                WorkflowStep(
                    step_id="step_3",
                    name="Generate Report",
                    agent_type=AgentType.EXECUTION,
                    task_template="Generate report from {analysis}",
                    required=False
                )
            ]
        )
        self.register_workflow(research_workflow)
        
        comprehensive_workflow = Workflow(
            workflow_id="comprehensive_flow",
            name="Comprehensive Analysis",
            description="Full analysis with multiple agents",
            steps=[
                WorkflowStep(
                    step_id="step_1",
                    name="Initial Research",
                    agent_type=AgentType.RESEARCH,
                    task_template="Research {topic}",
                    required=True,
                    parallel=True
                ),
                WorkflowStep(
                    step_id="step_2a",
                    name="Data Analysis",
                    agent_type=AgentType.ANALYSIS,
                    task_template="Analyze data {data}",
                    required=True,
                    parallel=True
                ),
                WorkflowStep(
                    step_id="step_2b",
                    name="Sentiment Analysis",
                    agent_type=AgentType.ANALYSIS,
                    task_template="Analyze sentiment {text}",
                    required=False,
                    parallel=True
                ),
                WorkflowStep(
                    step_id="step_3",
                    name="Synthesize Results",
                    agent_type=AgentType.COORDINATOR,
                    task_template="Combine {results}",
                    required=True
                )
            ]
        )
        self.register_workflow(comprehensive_workflow)
        
        support_workflow = Workflow(
            workflow_id="support_flow",
            name="Customer Support",
            description="Handle customer queries",
            steps=[
                WorkflowStep(
                    step_id="step_1",
                    name="Understand Query",
                    agent_type=AgentType.ANALYSIS,
                    task_template="Understand {query}",
                    required=True
                ),
                WorkflowStep(
                    step_id="step_2",
                    name="Research Solution",
                    agent_type=AgentType.RESEARCH,
                    task_template="Find solution for {problem}",
                    required=True
                ),
                WorkflowStep(
                    step_id="step_3",
                    name="Execute Response",
                    agent_type=AgentType.EXECUTION,
                    task_template="Respond with {solution}",
                    required=True
                )
            ]
        )
        self.register_workflow(support_workflow)
    
    def register_workflow(self, workflow: Workflow):
        self.workflows[workflow.workflow_id] = workflow
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict,
        user_id: int = 0
    ) -> OrchestrationResult:
        start_time = time.time()
        
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return OrchestrationResult(
                workflow_id=workflow_id,
                status="error",
                tasks_completed=0,
                total_tasks=0,
                duration_ms=0,
                results={},
                errors=[f"Workflow {workflow_id} not found"]
            )
        
        workflow_state = {
            "workflow_id": workflow_id,
            "user_id": user_id,
            "input_data": input_data,
            "step_results": {},
            "started_at": start_time
        }
        self.active_workflows[f"{workflow_id}_{user_id}"] = workflow_state
        
        results = {}
        errors = []
        completed = 0
        
        steps_to_run = []
        for step in workflow.steps:
            if step.parallel:
                steps_to_run.append((step, True))
            else:
                for prev_step in steps_to_run:
                    if not prev_step[1]:
                        break
                else:
                    steps_to_run.append((step, False))
        
        parallel_groups = []
        current_group = []
        
        for step, is_parallel in steps_to_run:
            if is_parallel:
                current_group.append(step)
            else:
                if current_group:
                    parallel_groups.append(current_group)
                    current_group = []
                parallel_groups.append([step])
        
        if current_group:
            parallel_groups.append(current_group)
        
        for group in parallel_groups:
            if len(group) > 1:
                tasks = await self._execute_parallel(group, input_data, results)
                for task_result in tasks:
                    if task_result.get("error"):
                        errors.append(task_result["error"])
                    else:
                        results[task_result["step_id"]] = task_result["output"]
                        completed += 1
            else:
                step = group[0]
                result = await self._execute_step(step, input_data, results)
                if result.get("error"):
                    errors.append(result["error"])
                else:
                    results[step.step_id] = result["output"]
                    completed += 1
        
        duration = (time.time() - start_time) * 1000
        
        self._execution_history.append({
            "workflow_id": workflow_id,
            "duration_ms": duration,
            "tasks_completed": completed,
            "errors": len(errors),
            "timestamp": time.time()
        })
        
        return OrchestrationResult(
            workflow_id=workflow_id,
            status="completed" if not errors else "partial",
            tasks_completed=completed,
            total_tasks=len(workflow.steps),
            duration_ms=duration,
            results=results,
            errors=errors
        )
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        input_data: Dict,
        previous_results: Dict
    ) -> Dict:
        task_id = f"task_{step.step_id}_{int(time.time() * 1000)}"
        
        agent = self.registry.find_available_agent([step.agent_type.value])
        if not agent:
            return {"error": f"No agent available for {step.agent_type.value}"}
        
        agent.current_tasks.append(task_id)
        
        try:
            template_filled = step.task_template
            for key, value in input_data.items():
                template_filled = template_filled.replace(f"{{{key}}}", str(value))
            for key, value in previous_results.items():
                template_filled = template_filled.replace(f"{{{key}}}", str(value))
            
            await asyncio.sleep(0.1)
            
            output = {
                "step_id": step.step_id,
                "agent": agent.name,
                "result": f"Executed: {template_filled}",
                "timestamp": time.time()
            }
            
            agent.current_tasks.remove(task_id)
            agent.completed_tasks += 1
            
            return {"output": output}
            
        except Exception as e:
            agent.current_tasks.remove(task_id)
            return {"error": str(e)}
    
    async def _execute_parallel(
        self,
        steps: List[WorkflowStep],
        input_data: Dict,
        previous_results: Dict
    ) -> List[Dict]:
        tasks = [
            self._execute_step(step, input_data, previous_results)
            for step in steps
        ]
        return await asyncio.gather(*tasks)
    
    async def execute_single_task(
        self,
        task_name: str,
        required_capabilities: List[str],
        input_data: Dict
    ) -> Dict:
        task_id = f"task_{int(time.time() * 1000)}"
        
        agent = self.registry.find_available_agent(required_capabilities)
        if not agent:
            return {"error": "No available agent", "task_id": task_id}
        
        task = Task(
            task_id=task_id,
            name=task_name,
            description=task_name,
            required_capabilities=required_capabilities,
            input_data=input_data
        )
        
        self.task_queue.add_task(task)
        
        task = self.task_queue.get_next_task()
        if not task:
            return {"error": "Failed to get task", "task_id": task_id}
        
        agent.current_tasks.append(task_id)
        
        try:
            await asyncio.sleep(0.2)
            
            output = {"result": f"Task {task_name} completed", "data": input_data}
            
            self.task_queue.complete_task(task_id, output)
            agent.current_tasks.remove(task_id)
            agent.completed_tasks += 1
            
            return {"success": True, "task_id": task_id, "output": output}
            
        except Exception as e:
            self.task_queue.fail_task(task_id, str(e))
            agent.current_tasks.remove(task_id)
            return {"error": str(e), "task_id": task_id}
    
    def get_workflows(self) -> List[Dict]:
        return [
            {
                "id": w.workflow_id,
                "name": w.name,
                "description": w.description,
                "steps": [{"id": s.step_id, "name": s.name, "parallel": s.parallel} for s in w.steps]
            }
            for w in self.workflows.values()
        ]
    
    def get_agents(self) -> List[Dict]:
        return self.registry.get_all_agents()
    
    def get_orchestrator_stats(self) -> Dict:
        return {
            "total_agents": len(self.registry.agents),
            "active_workflows": len(self.active_workflows),
            "pending_tasks": self.task_queue.get_pending_count(),
            "running_tasks": self.task_queue.get_running_count(),
            "workflows_available": len(self.workflows),
            "recent_executions": len(self._execution_history)
        }
    
    def get_execution_history(self, limit: int = 10) -> List[Dict]:
        return list(self._execution_history)[-limit:]


agent_orchestrator = AgentOrchestrator()