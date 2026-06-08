"""
Planning Agent
==============
Decomposes complex, multi-step goals into executable plans
and coordinates specialized sub-agents to fulfill each step.

This is the "brain" of the system for complex tasks. Instead of
throwing a query at a single agent, it:
  1. Analyzes the goal
  2. Creates an ordered plan (with parallel steps where possible)
  3. Delegates each step to the best agent
  4. Aggregates results into a coherent response

Examples of complex goals this handles:
  "Research quantum computing, write a summary, then save it to a file"
  "Open Chrome, go to Gmail, and read my latest emails"
  "Find the best Python job listings and create a tailored CV"
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Tuple

from .base import BaseAgent

logger = logging.getLogger(__name__)


class PlanStep:
    """A single step in an execution plan."""

    def __init__(
        self,
        step_id: str,
        description: str,
        agent_type: str,
        tools: List[str],
        depends_on: List[str],  # step_ids this step waits for
        input_template: str,    # how to phrase the request to the agent
    ):
        self.step_id = step_id
        self.description = description
        self.agent_type = agent_type
        self.tools = tools
        self.depends_on = depends_on
        self.input_template = input_template
        self.status = "pending"  # pending | running | done | failed
        self.result: Optional[str] = None
        self.error: Optional[str] = None
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None


class ExecutionPlan:
    """An ordered, potentially parallel execution plan."""

    def __init__(self, goal: str, steps: List[PlanStep]):
        self.plan_id = str(uuid.uuid4())[:8]
        self.goal = goal
        self.steps: List[PlanStep] = steps
        self.created_at = time.time()
        self.status = "pending"
        self.final_response: Optional[str] = None

    def get_ready_steps(self) -> List[PlanStep]:
        """Return steps that are ready to execute (all dependencies complete)."""
        ready = []
        completed_ids = {s.step_id for s in self.steps if s.status == "done"}

        for step in self.steps:
            if step.status == "pending":
                if all(dep in completed_ids for dep in step.depends_on):
                    ready.append(step)
        return ready

    def is_complete(self) -> bool:
        return all(s.status in ("done", "failed") for s in self.steps)

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "status": self.status,
            "steps": [
                {
                    "step_id": s.step_id,
                    "description": s.description,
                    "agent": s.agent_type,
                    "status": s.status,
                    "result_preview": (s.result or "")[:100],
                    "error": s.error,
                    "duration_ms": round((s.completed_at - s.started_at) * 1000, 1)
                    if s.started_at and s.completed_at else None,
                }
                for s in self.steps
            ],
        }


class PlanningAgent(BaseAgent):
    name = "Planning Agent"
    description = (
        "Breaks down complex multi-step goals into plans and coordinates "
        "multiple specialized agents to execute each step."
    )
    tools = [
        "create_plan",
        "execute_plan",
        "get_plan_status",
        "cancel_plan",
        "list_plans",
    ]

    PLANNER_PROMPT = """You are the Planning Agent for Daffodil Intelligence.
Your job is to decompose a complex user goal into a clear, executable plan.

Available agent types:
- academic: CGPA, grades, courses, attendance, results
- library: books, journals, research papers, PDF
- career: jobs, internships, CV analysis, career roadmap
- coding: debug code, generate code, explain code
- research: academic papers, thesis help, citations
- wellness: mental health, study tips, stress
- finance: fees, scholarships, payments, waivers
- vision: analyze images, screenshots, PDFs
- computer_use: control mouse/keyboard, screen automation
- copycat: record and replay user actions
- browser: web search, open URLs, scrape pages
- file: read/write files, list directories
- general: greetings, clarifications, general info

Output a JSON plan with this exact format:
{
  "analysis": "brief analysis of the goal",
  "steps": [
    {
      "step_id": "s1",
      "description": "what this step does",
      "agent_type": "agent_name",
      "tools": ["tool1", "tool2"],
      "depends_on": [],
      "input_template": "exact instruction to send to the agent"
    },
    {
      "step_id": "s2", 
      "description": "...",
      "agent_type": "...",
      "tools": [],
      "depends_on": ["s1"],
      "input_template": "..."
    }
  ]
}

Rules:
- Independent steps should have empty depends_on (they run in parallel)
- Steps that need results from previous steps should list those step_ids in depends_on
- Keep steps atomic and focused
- Choose the most specific agent for each step
- Limit to 8 steps maximum
- Return ONLY the JSON, no other text
"""

    SYNTHESIZER_PROMPT = """You are synthesizing the results from a multi-step AI plan.
The user's original goal was: {goal}

The following steps were executed and their results are:
{results}

Please combine these results into a single, coherent, helpful response for the user.
Respond in the same language as the original goal (English or Bengali).
"""

    def __init__(self):
        super().__init__()
        self._active_plans: Dict[str, ExecutionPlan] = {}

    async def process(self, message: str, context: Optional[dict] = None) -> str:
        """
        Main entry point. Detects if this needs planning or can be answered directly.
        Complex multi-step queries get planned; simple ones route directly.
        """
        # Check complexity — simple queries don't need planning
        if self._is_simple_query(message):
            # Route directly to supervisor instead
            from .supervisor import SupervisorAgent
            supervisor = SupervisorAgent()
            return await supervisor.process(message, context)

        # Create and execute a plan
        try:
            plan = await self._create_plan(message)
            if not plan or not plan.steps:
                # Planning failed, fall back to direct routing
                from .supervisor import SupervisorAgent
                supervisor = SupervisorAgent()
                return await supervisor.process(message, context)

            self._active_plans[plan.plan_id] = plan

            # Execute the plan
            result = await self._execute_plan(plan, context)
            return result

        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return f"I had trouble creating a plan for that goal. Let me try directly: {await self.generate_response('You are a helpful assistant.', message)}"

    async def create_and_execute(self, goal: str, context: Optional[dict] = None) -> Tuple[ExecutionPlan, str]:
        """Create a plan, execute it, and return both the plan and the result."""
        plan = await self._create_plan(goal)
        if not plan:
            return None, "Could not create execution plan"

        self._active_plans[plan.plan_id] = plan
        result = await self._execute_plan(plan, context)
        return plan, result

    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        return self._active_plans.get(plan_id)

    def list_plans(self) -> List[dict]:
        return [p.to_dict() for p in self._active_plans.values()]

    # ─── Private ─────────────────────────────────────────────────────────────

    def _is_simple_query(self, message: str) -> bool:
        """Heuristic: is this a simple single-agent query?"""
        msg_lower = message.lower()

        # Multi-step indicators
        multi_step_signals = [
            " then ", " after that ", " and then ", " next ", " finally ",
            " first ", " second ", " step ", "তারপর", "পরে", "এরপর",
            "multiple", "also", "additionally", "furthermore",
        ]

        # If message has connectors, it's multi-step
        if any(s in msg_lower for s in multi_step_signals):
            return False

        # If very short, it's probably simple
        if len(message.split()) < 8:
            return True

        return True  # Default: use direct routing, only plan for explicit multi-step

    async def _create_plan(self, goal: str) -> Optional[ExecutionPlan]:
        """Use LLM to create a structured execution plan."""
        try:
            raw = await self.generate_response(self.PLANNER_PROMPT, goal)

            # Parse JSON from response
            raw = raw.strip()
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            data = json.loads(raw)
            steps_data = data.get("steps", [])

            steps = []
            for s in steps_data:
                step = PlanStep(
                    step_id=s.get("step_id", f"s{len(steps)+1}"),
                    description=s.get("description", ""),
                    agent_type=s.get("agent_type", "general"),
                    tools=s.get("tools", []),
                    depends_on=s.get("depends_on", []),
                    input_template=s.get("input_template", goal),
                )
                steps.append(step)

            return ExecutionPlan(goal=goal, steps=steps)

        except json.JSONDecodeError as e:
            logger.error(f"Plan JSON parse failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Plan creation failed: {e}")
            return None

    async def _execute_plan(self, plan: ExecutionPlan, context: Optional[dict]) -> str:
        """Execute all plan steps, respecting dependencies, running parallel where possible."""
        from .supervisor import AGENT_MAP

        plan.status = "running"
        results: Dict[str, str] = {}

        # Execute in waves (steps with same dependency level run in parallel)
        max_waves = 10
        for wave in range(max_waves):
            ready = plan.get_ready_steps()
            if not ready:
                if plan.is_complete():
                    break
                # Deadlock / all remaining failed
                logger.warning(f"Plan {plan.plan_id}: no ready steps but plan not complete")
                break

            # Run all ready steps in parallel
            tasks = []
            for step in ready:
                step.status = "running"
                step.started_at = time.time()

                # Get the result template, filling in results from dependencies
                instruction = step.input_template
                for dep_id in step.depends_on:
                    dep_result = results.get(dep_id, "")
                    instruction = instruction.replace(f"{{{dep_id}}}", dep_result[:200])

                agent_type = step.agent_type
                agent = AGENT_MAP.get(agent_type) or AGENT_MAP.get("general")
                task = asyncio.create_task(
                    self._execute_step(step, agent, instruction, context)
                )
                tasks.append(task)

            await asyncio.gather(*tasks)

            # Collect results
            for step in ready:
                if step.result:
                    results[step.step_id] = step.result

        # Synthesize final response
        plan.status = "completed"
        result_text = "\n\n".join([
            f"**Step {s.step_id} ({s.description}):**\n{s.result or s.error or 'No result'}"
            for s in plan.steps
        ])

        synthesizer_prompt = self.SYNTHESIZER_PROMPT.format(
            goal=plan.goal,
            results=result_text,
        )

        try:
            final = await self.generate_response(synthesizer_prompt, plan.goal)
            plan.final_response = final
            return final
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return result_text

    async def _execute_step(
        self,
        step: PlanStep,
        agent,
        instruction: str,
        context: Optional[dict],
    ):
        """Execute a single plan step."""
        try:
            result = await agent.process(instruction, context)
            step.result = result
            step.status = "done"
        except Exception as e:
            logger.error(f"Step {step.step_id} failed: {e}")
            step.error = str(e)
            step.status = "failed"
        finally:
            step.completed_at = time.time()
