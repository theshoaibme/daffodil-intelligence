# ... existing imports ...
from .celery_app import celery_app
import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from telegram import Bot

logger = logging.getLogger(__name__)

async def send_telegram_notification(chat_id: int, text: str):
    """Helper to send a proactive Telegram message."""
    from app.core.config import get_settings
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("Telegram Bot Token not configured.")
        return
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")

@celery_app.task(bind=True, name="agent_tasks.send_university_reminders")
def send_university_reminders(self):
    """
    Automation task to send:
    1. Tomorrow's routine reminder (Daily)
    2. Class/Exam reminder 1 hour before (Hourly check)
    """
    # Run async logic in a new loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_execute_reminders())
    finally:
        loop.close()

async def _execute_reminders():
    # Load Telegram users
    users_path = "/home/kali/Desktop/daffodil-intelligence/apps/api/telegram_users.json"
    if not os.path.exists(users_path):
        return
    with open(users_path, 'r') as f:
        users = json.load(f)

    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    
    # Mock Routine for 64_I Section CSE
    routine_64_i = {
        "Monday": [{"time": "10:00 AM", "course": "CSE321", "room": "401", "teacher": "Prof. Rahman"}],
        "Tuesday": [{"time": "11:00 AM", "course": "CSE322", "room": "205", "teacher": "Prof. Karim"}],
        "Wednesday": [{"time": "09:00 AM", "course": "CSE323", "room": "102", "teacher": "Prof. Islam"}],
        "Thursday": [{"time": "01:00 PM", "course": "CSE324", "room": "C-401", "teacher": "Prof. Ahmed"}],
        "Friday": [],
        "Saturday": [],
        "Sunday": [],
    }

    for uid, user_data in users.items():
        chat_id = user_data.get("telegram_id")
        if not chat_id: continue
        
        # 1. Tomorrow's Routine Reminder (trigger this at 9 PM)
        if now.hour == 21: 
            day_name = tomorrow.strftime("%A")
            day_routine = routine_64_i.get(day_name, [])
            if day_routine:
                msg = f"📅 *Tomorrow's Routine ({day_name})*\n\n"
                for r in day_routine:
                    msg += f"⏰ {r['time']} - {r['course']} (Room: {r['room']}, Teacher: {r['teacher']})\n"
                await send_telegram_notification(chat_id, msg)

        # 2. Class Reminder (1 hour before)
        # Check today's routine
        day_name = now.strftime("%A")
        today_routine = routine_64_i.get(day_name, [])
        for r in today_routine:
            # Simple time check (mock logic)
            # In a real app, we'd parse '10:00 AM' to a datetime object
            pass

    logger.info("University reminders processed.")

@celery_app.task(bind=True, name="agent_tasks.run_agent")
def run_agent_task(self, agent_type: str, message: str, user_id: int, session_id: str):
    """
    Execute an agent task in the background.
    Results are stored in Celery result backend and can be polled.
    """
    self.update_state(state="RUNNING", meta={"agent": agent_type, "status": "processing"})

    try:
        from app.agents.supervisor import AGENT_MAP
        agent = AGENT_MAP.get(agent_type) or AGENT_MAP.get("general")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(agent.process(message))
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
