from .celery_app import celery_app
import asyncio
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="agent_tasks.send_university_reminders")
def send_university_reminders(self):
    """Hourly tick: due reminders + class routine Telegram notifications."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        from app.automation.scheduler_logic import run_automation_tick

        result = loop.run_until_complete(run_automation_tick())
        logger.info("Automation tick: %s", result)
        return result
    finally:
        loop.close()


@celery_app.task(bind=True, name="agent_tasks.run_agent")
def run_agent_task(self, agent_type: str, message: str, user_id: int, session_id: str):
    """Execute an agent task in the background."""
    self.update_state(state="RUNNING", meta={"agent": agent_type, "status": "processing"})

    try:
        from app.agents.supervisor import AGENT_MAP

        agent = AGENT_MAP.get(agent_type) or AGENT_MAP.get("general")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(agent.process(message, {"user_id": user_id}))
        finally:
            loop.close()

        return {
            "agent": agent_type,
            "message": message,
            "result": result,
            "user_id": user_id,
            "session_id": session_id,
        }
    except Exception as e:
        logger.error(f"Agent task failed: {e}")
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise


@celery_app.task(bind=True, name="agent_tasks.run_plan")
def run_plan_task(self, goal: str, user_id: int):
    """Execute a multi-step planning task in the background."""
    self.update_state(state="RUNNING", meta={"goal": goal, "status": "planning"})

    try:
        from app.agents.planning import PlanningAgent

        agent = PlanningAgent()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            plan, result = loop.run_until_complete(agent.create_and_execute(goal))
        finally:
            loop.close()

        return {
            "goal": goal,
            "plan": plan.to_dict() if plan else None,
            "result": result,
            "user_id": user_id,
        }
    except Exception as e:
        logger.error(f"Plan task failed: {e}")
        raise
