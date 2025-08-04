import pymysql
import requests
import base64
import mimetypes
import os

class ModelHelper:
    def __init__(self, model_name):
        connection = pymysql.connect(
            host="localhost",
            user=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PWD"],
            db=os.environ["MYSQL_DB"]
        )

        cursor = connection.cursor()

        # Fetch host and port for the model
        connection_prompt = f"SELECT host, port FROM models WHERE name = '{model_name}' LIMIT 1"
        cursor.execute(connection_prompt)
        connection_object = cursor.fetchone()

        if not connection_object:
            raise ValueError(f"Model '{model_name}' not found in database.")

        host, port = connection_object

        self.url = f"http://{host}:{port}/v1/chat/completions"
        self.model_name = model_name

    def query_model(self, query, image=None):
        # Prepare messages based on whether an image is provided
        if image is None:
            messages = [{
                "role": "user",
                "content": query
            }]
        else:
            if not os.path.isfile(image):
                raise FileNotFoundError(f"Image file '{image}' not found.")

            # Read and encode image as base64
            with open(image, "rb") as image_file:
                image_bytes = image_file.read()
                image_b64 = base64.b64encode(image_bytes).decode('utf-8')

            mime_type, _ = mimetypes.guess_type(image)
            if mime_type is None:
                mime_type = "image/png"

            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": query
                    }
                ]
            }]

        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.7
        }

        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            raise RuntimeError(f"Request to model failed: {e}")
        except KeyError:
            raise ValueError(f"Unexpected response format: {response.text}")