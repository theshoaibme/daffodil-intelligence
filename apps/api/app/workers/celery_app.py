"""
Celery App — Background Task Worker
=====================================
Celery configuration for long-running agent tasks.
Workers can be scaled horizontally by running:
  celery -A app.workers.celery_app worker --loglevel=info

Monitor with Flower:
  celery -A app.workers.celery_app flower --port=5555
"""

from celery import Celery
from celery.schedules import crontab
from ..core.config import get_settings


def create_celery_app() -> Celery:
    settings = get_settings()

    app = Celery(
        "daffodil_intelligence",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=[
            "app.workers.agent_tasks",
            "app.workers.computer_tasks",
        ],
    )

    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="Asia/Dhaka",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_soft_time_limit=300,   # 5 minutes
        task_time_limit=600,        # 10 minutes hard limit
        result_expires=3600,        # Results expire in 1 hour
        task_routes={
            "app.workers.computer_tasks.*": {"queue": "computer"},
            "app.workers.agent_tasks.*": {"queue": "agents"},
        },
        beat_schedule={
            "automation-hourly": {
                "task": "agent_tasks.send_university_reminders",
                "schedule": crontab(minute=0),
            },
        },
    )

    return app


celery_app = create_celery_app()
