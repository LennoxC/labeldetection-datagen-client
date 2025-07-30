from celery import Celery
from celeryconfig import broker_url, result_backend
import time
import redis
import pymysql
import os
from src.datasets.loader import Loader
from src.datasets.food.foodloader import FoodLoader

celery_app = Celery("tasks", broker=broker_url, backend=result_backend)

@celery_app.task(bind=True)
def data_processing(self, mode):
    redis_client = redis.Redis(host='localhost', port=6379, db=2)
    connection = pymysql.connect(
        host="localhost",
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PWD"],
        db=os.environ["MYSQL_DB"]
    )
    cursor = connection.cursor()

    path = cursor.execute(f"SELECT path FROM Applications WHERE name = '{mode}' LIMIT 1")

    task_id = self.request.id
    redis_client.set(f"status:{task_id}", "Started")
    redis_client.delete(f"logs")

    if mode == "food":
        loader = FoodLoader(path)
        loader.load()

    for i in range(10):
        redis_client.rpush(f"logs:{task_id}", f"Step {i} done")
        time.sleep(1)

    redis_client.set(f"status:{task_id}", "Completed")


'''
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--dataset_location", type=str, help="Base path of the dataset files for reading/writing to.")
    parser.add_argument("-m", "--mode", type=str, help="Which dataset mode? Choose from 'food', 'pharma', 'wine'.")
    parser.add_argument("-v", "--verbose", action='store_true', help="Enable verbose output")

    args = parser.parse_args()

    if args.verbose:
        log_level=logging.DEBUG
    else:
        log_level=logging.INFO

    setup_logging(level=log_level)

    dataset_location = args.dataset_location
    mode = args.mode
    path = os.path.join(dataset_location, "labeldetection-datagen-client", mode)

    if mode == "food":
        loader = FoodLoader(path)
    elif mode == "wine":
        loader = WineLoader(path)
    else:
        logging.critical("Invalid mode. Choose from 'food' or 'wine'")
        exit(0)

    loader.load()
'''
