from celery import Celery
import os

# Initialize Celery
celery_app = Celery(
    "pinnacle_copilot",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
    worker_concurrency=os.cpu_count(),
)

# Optional: Configure task routing
celery_app.conf.task_routes = {
    "pinnacle_copilot.tasks.*": {"queue": "default"},
}

# Optional: Configure task defaults
celery_app.conf.task_default_queue = "default"
celery_app.conf.task_default_exchange = "default"
celery_app.conf.task_default_routing_key = "default"
