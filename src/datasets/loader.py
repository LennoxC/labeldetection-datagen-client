from abc import ABC, abstractmethod
import logging
import pymysql
import os

class Loader:
    def __init__(self, dataset):
        self.dataset = dataset
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.dataset_id = None
        # insert into datasets

        self.create_sql_dataset()

    # load an image
    @abstractmethod
    def load(self):
        pass

    # sample some prompts
    @abstractmethod
    def prompts(self):
        pass

    # package to a query
    @abstractmethod
    def package(self):
        pass

    # run OCR
    def ocr(self):
        pass

    def create_sql_dataset(self):
        connection = pymysql.connect(
            host="localhost",
            user=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PWD"],
            db=os.environ["MYSQL_DB"]
        )

        cursor = connection.cursor()

        # get the application id and base path
        app_query = f"SELECT id, name, path, leading_prompt, middle_prompt, trailing_prompt FROM applications WHERE name = '{self.dataset}' LIMIT 1"

        cursor.execute(app_query)

        application_details = cursor.fetchone()

        application_id = application_details[0]
        application_name = application_details[1]
        application_path = application_details[2]
        application_leading_prompt = application_details[3]
        application_middle_prompt = application_details[4]
        application_trailing_prompt = application_details[5]

        auto_description = f"{application_name} dataset, \nLeading prompt: {application_leading_prompt}, \n Middle prompt: {application_middle_prompt}, \n Trailing prompt: {application_trailing_prompt}"

        dataset_insert = f"INSERT INTO datasets (application_id, auto_description) VALUES ({application_id}, '{auto_description}')"

        cursor.execute(dataset_insert)
        connection.commit()

        self.dataset_id = cursor.lastrowid

        print(f"Dataset id: {self.dataset_id}")
