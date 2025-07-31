# celery -A celery_worker.celery_app worker --loglevel=info
from tasks import celery_app