import pymysql
import os

class SqlHelper:
    def __init__(self):
        connection = pymysql.connect(
            host="localhost",
            user=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PWD"],
            db=os.environ["MYSQL_DB"]
        )
        cursor = connection.cursor()

        self.cursor = cursor

    def execute_one_liner(self, query):
        cursor = self.cursor
        cursor.execute(query)
        return cursor.fetchone()

    def get_cursor(self):
        return self.cursor