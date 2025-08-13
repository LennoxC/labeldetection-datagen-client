import gzip
import random
import urllib.request
from datasets.loader import Loader
import uuid
import os
import shutil
from model_helper import ModelHelper
import pandas as pd

class FoodLoader(Loader):
    def __init__(self, task_id):
        super(FoodLoader, self).__init__("food", task_id)

        self.set_status("Setting up food loader.")

        self.add_logs("Food loader created. Creating directories...")

        self.images_dir =   os.path.join(self.data_location, "images") # /food/images
        self.ocr_dir =      os.path.join(self.data_location, "ocr") # /food/ocr
        self.metadata_dir = os.path.join(self.data_location, "metadata")
        self.output_dir =   os.path.join(self.data_location, "output")

        self.results_csv_path = os.path.join(self.data_location, "outputs.csv")

        # specific to food dataset AWS download
        self.bucket_url = "https://openfoodfacts-images.s3.eu-west-3.amazonaws.com/"
        data_keys_url = self.bucket_url + "data/data_keys.gz"
        self.local_keys_file = f"{self.metadata_dir}/data_keys.gz"

        if not os.path.exists(self.data_location):
            self.add_logs("Created path: " + self.data_location)
            os.makedirs(self.data_location)

        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.ocr_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)

        self.make_results_csv(self.results_csv_path)

        if not os.path.exists(self.local_keys_file):
            self.add_logs(f"Downloading data keys file: {data_keys_url}")
            urllib.request.urlretrieve(data_keys_url, self.local_keys_file)

        self.add_logs("Setup complete.")

        self.set_status("Ready for dataset generation.")

        self.prompts = self.get_prompts_df()

    # load an image
    def load(self):
        return self.download()

    # sample some prompts
    def process(self, image_path):
        return self.do_processing(image_path) # return a tuple

    # package to a query
    def save(self, query, image_path, answer, datapoint_id):
        return self.save_to_output(query, image_path, answer, datapoint_id)

    # --------------- non inherited methods (custom application specific logic) ---------------

    def download(self):
        self.logger.debug("Sampling a random food image.")
        with gzip.open(self.local_keys_file, 'rt') as f:
            all_keys = [line.strip() for line in f]

        sampled_keys = random.sample(all_keys, 1)

        for key in sampled_keys:

            self.logger.debug(f"Downloading food image {key}")

            image_url = self.bucket_url + key

            datapoint_id = uuid.uuid4()

            image_name = f"{datapoint_id}.jpg"
            image_path = os.path.join(self.images_dir, image_name)

            try:
                self.logger.debug(f"Downloading image: {image_url} -> {image_path}")
                urllib.request.urlretrieve(image_url, image_path)

                return image_path, datapoint_id
            except Exception as e:
                self.logger.critical(f"Failed to download image {image_url}: {e}")

        return None, None

    def do_processing(self, image_path):
        # form a query for an AI model

        prompt_opening = self.get_prompt("Food feature extraction preamble")
        prompt_closing = self.get_prompt("Food feature extraction closing")

        image_features = self.get_image_prompts("food")

        string_features = []

        for image_feature in image_features:
            string_features.append(f"{{feature: \"{image_feature[0]}\", json_name: \"{image_feature[1]}\"}}")

        prompt = f"""
                  {prompt_opening} \n
                  [ \n
                  {",\n".join(string_features)} \n
                  ] \n
                  {prompt_closing}
                  """

        model = ModelHelper("AIDC-AI/Ovis2-4B")

        response = model.query_model(prompt, image=image_path)

        return prompt, response

    def save_to_output(self, query, image_path, answer, datapoint_id):
        datapoint_id = str(datapoint_id)
        image_name = os.path.basename(image_path)
        prompts = self.prompts

        properties = self.parse_response(answer, "result1")

        df = pd.merge(prompts, properties, left_on="json_property", right_on="property")

        df["image_name"] = image_name
        df["datapoint_id"] = datapoint_id
        df["dataset"] = self.dataset
        df["result2"] = df["result1"]
        df["matches"] = (df["result1"] == df["result2"])
        df["result"] = df["result1"]

        df = df[["datapoint_id", "image_name", "dataset", "property", "prompt", "json_placeholder", "result1", "result2", "matches", "result"]]

        df = self.filter_nans(df)

        df.to_csv(self.results_csv_path, mode="a", header=False, index=False)

        self.increment_images()