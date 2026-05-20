from celery import Celery
import httpx
import asyncio

celery_app = Celery("di_worker", broker="redis://localhost:6379", backend="redis://localhost:6379")


@celery_app.task
def process_chat_message(user_id: int, message: str):
    import time
    time.sleep(1)
    return {"user_id": user_id, "response": f"Processed: {message[:50]}..."}


@celery_app.task
def generate_embeddings(text: str):
    return {"embedding": [0.1] * 1536}


@celery_app.task
def send_notification(user_id: int, title: str, body: str):
    return {"sent": True, "user_id": user_id}


@celery_app.task
def cleanup_old_sessions():
    return {"cleaned": 10}


@celery_app.task
def sync_external_data():
    return {"synced": True}


if __name__ == "__main__":
    celery_app.start()