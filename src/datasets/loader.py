from abc import ABC, abstractmethod
import logging
import pymysql
import redis
from datetime import datetime
import uuid
import os
import pandas as pd
import json
import ast

class Loader:
    def __init__(self, dataset, task_id):
        self.dataset = dataset
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.dataset_id = None
        self.data_location = None
        # insert into datasets

        self.task_id = task_id
        self.redis_client = redis.Redis(host='localhost', port=6379, db=2)

        self.images_count = 0
        self.target_size = 0
        self.uuid = uuid.uuid4()

        self.create_sql_dataset()

    def start(self):
        self.set_status("Running")
        self.add_logs(f"Targeting a dataset of {self.target_size} images.")
        while self.images_count < self.target_size:
            try:
                # load an image, return its file path
                image_path, datapoint_id = self.load()

                if image_path is None:
                    self.add_logs("Image path not found, re-processing")
                    continue

                # process the image, return a query, imagepath, answer
                query, answer = self.process(image_path)
                # save the image, query, answer
                self.save(query, image_path, answer, datapoint_id)

                # logging
                self.add_logs(f"Image Processing {100 * (self.images_count / self.target_size)}% complete: {self.images_count}/{self.target_size}")
            except Exception as e:
                self.add_logs(f"Exception thrown: {str(e)}")

    # load an image
    @abstractmethod
    def load(self):
        return None, None

    # sample some prompts
    @abstractmethod
    def process(self, image_path):
        return None, None

    # package to a query
    @abstractmethod
    def save(self, query, image_path, answer, datapoint_id):
        pass

    # run OCR
    def ocr(self):
        pass

    def increment_images(self):
        self.images_count += 1

    def set_status(self, message):
        self.redis_client.set(f"status:{self.task_id}", message)

    def add_logs(self, message):
        self.redis_client.rpush(f"logs:{self.task_id}", message)

    def get_cursor(self):
        connection = pymysql.connect(
            host="localhost",
            user=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PWD"],
            db=os.environ["MYSQL_DB"]
        )

        return connection.cursor()

    def get_prompt(self, prompt_name):
        cursor = self.get_cursor()

        # get the application id and base path
        query = f"SELECT prompt FROM prompts WHERE name = '{prompt_name}' LIMIT 1"

        cursor.execute(query)

        prompt = cursor.fetchone()[0]

        return prompt

    def get_image_prompts(self, application):
        cursor = self.get_cursor()

        query = f"""
                SELECT prompt, json_property, json_placeholder
                FROM image_prompts AS img
                LEFT JOIN applications AS app ON img.application_id = app.id
                WHERE app.name = '{self.dataset}'
                """

        cursor.execute(query)
        prompts = cursor.fetchall()

        return prompts

    def create_sql_dataset(self):
        connection = pymysql.connect(
            host="localhost",
            user=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PWD"],
            db=os.environ["MYSQL_DB"]
        )

        cursor = connection.cursor()

        # get the application id and base path
        app_query = f"SELECT id, name, path, target_size FROM applications WHERE name = '{self.dataset}' LIMIT 1"

        cursor.execute(app_query)

        application_details = cursor.fetchone()

        application_id = application_details[0]
        application_name = application_details[1]
        application_path = application_details[2]
        application_target_size = application_details[3]

        auto_description = f"{application_name} dataset, initialized {datetime.now()}. Target size {application_target_size} images."

        dataset_insert = f"INSERT INTO datasets (application_id, uuid, auto_description) VALUES ({application_id}, '{self.uuid}', '{auto_description}')"

        cursor.execute(dataset_insert)
        connection.commit()

        self.dataset_id = cursor.lastrowid
        self.target_size = application_target_size

        self.data_location = os.path.join(application_path, str(self.uuid))

    def make_results_csv(self, filepath):
        columns = ["datapoint_id", "image_name", "dataset", "property", "prompt", "json_placeholder", "result1", "result2", "matches", "result"]  # Replace with your actual column names
        df = pd.DataFrame(columns=columns)
        df.to_csv(filepath, index=False)


    def get_prompts_df(self):
        cursor = self.get_cursor()

        query = f"""
                SELECT prompt, json_property, json_placeholder
                FROM image_prompts AS img
                LEFT JOIN applications AS app ON img.application_id = app.id
                WHERE app.name = '{self.dataset}'
                """

        cursor.execute(query)
        prompts = cursor.fetchall()

        columns = [desc[0] for desc in cursor.description]

        return pd.DataFrame(prompts, columns=columns)

    def safe_parse_json(self, json_str):
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            try:
                json_str = json_str.strip()
                cleaned = json_str.replace("'", '"').strip().rstrip(',')
                return json.loads(cleaned)
            except json.JSONDecodeError:
                try:
                    return ast.literal_eval(json_str)
                except (ValueError, SyntaxError):
                    print("Failed to parse JSON.")
                    return {}

    def parse_response(self, json_str, expert):
        json_obj = self.safe_parse_json(json_str)

        if isinstance(json_obj, dict):
            return pd.DataFrame(list(json_obj.items()), columns=["property", expert])
        else:
            return pd.DataFrame(columns=["property", expert])

    def filter_nans(self, df):
        nan_values = ["nan", "NaN", None, "", " "]

        df = df[~df['result1'].isin(nan_values)]
        df = df[~df['result2'].isin(nan_values)]
        df = df[~df['result'].isin(nan_values)]

        return df
