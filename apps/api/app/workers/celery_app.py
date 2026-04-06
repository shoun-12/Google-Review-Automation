from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "google_review_automation",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.autodiscover_tasks(["app.workers"])

celery_app.conf.beat_schedule = {
    "sync-google-accounts": {
        "task": "app.workers.tasks.sync_all_google_accounts",
        "schedule": 900.0,
    }
}

celery_app.conf.timezone = "UTC"
