from celery import Celery
from celeryconfig import broker_url, result_backend
import time
import redis
import pymysql
import os
from datasets.food.foodloader import FoodLoader
from datetime import datetime
import json
from dotenv import load_dotenv

load_dotenv()
celery_app = Celery("tasks", broker=broker_url, backend=result_backend)

@celery_app.task(bind=True)
def data_processing_task(self, mode):
    print("started task")
    redis_client = redis.Redis(host='localhost', port=6379, db=2)
    task_id = self.request.id
    start_time = datetime.utcnow().isoformat()

    # Add job summary to a Redis list
    job_info = {
        "task_id": task_id,
        "name": f"{mode.title()} Processing",
        "started_at": start_time,
        "mode": mode
    }
    redis_client.lpush("job_list", json.dumps(job_info))  # Store latest jobs

    # Set status and initialize logs
    redis_client.set(f"status:{task_id}", "Setting up...")
    redis_client.delete(f"logs:{task_id}")

    # Find the path from the database
    connection = pymysql.connect(
        host="localhost",
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PWD"],
        db=os.environ["MYSQL_DB"]
    )
    cursor = connection.cursor()
    cursor.execute("SELECT path FROM applications WHERE name = %s LIMIT 1", (mode,))
    path_result = cursor.fetchone()
    path = path_result[0] if path_result else None

    if mode == "food" and path:
        loader = FoodLoader(task_id)
        loader.load()

    redis_client.set(f"status:{task_id}", "Completed")

