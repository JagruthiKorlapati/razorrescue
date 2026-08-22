from celery import Celery
from app.config import REDIS_URL

celery_app = Celery(
    "razorrescue",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.retry_scheduler"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)