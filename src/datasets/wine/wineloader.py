import random
import shutil
import uuid
import pandas as pd

from datasets.loader import Loader
import os

from model_helper import ModelHelper

class WineLoader(Loader):
    def __init__(self, task_id):
        super(WineLoader, self).__init__("wine", task_id)

        self.set_status("Setting up wine loader.")

        self.add_logs("Wine loader created. Creating directories...")

        self.images_dir = os.path.join(self.data_location, "images")  # /wine/images
        self.output_dir = os.path.join(self.data_location, "output")
        self.images_source_dir = os.path.join(self.application_path, "data")

        self.results_csv_path = os.path.join(self.data_location, "outputs.csv")

        self.images_list = [f for f in os.listdir(self.images_source_dir) if os.path.isfile(os.path.join(self.images_source_dir, f))]

        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.images_source_dir, exist_ok=True)

        self.make_results_csv(self.results_csv_path)

        self.add_logs("Setup complete.")

        self.set_status("Ready for dataset generation.")

        self.prompts = self.get_prompts_df()

    # load an image
    def load(self):
        return self.download()

    # sample some prompts
    def process(self, image_path):
        return self.do_processing(image_path)  # return a tuple

    # package to a query
    def save(self, query, image_path, answer, datapoint_id):
        return self.save_to_output(query, image_path, answer, datapoint_id)

    def download(self):
        datapoint_id = uuid.uuid4()
        new_image_name = f"{datapoint_id}.jpg"

        wine_image = random.choice(self.images_list)
        wine_image_path = os.path.join(self.images_source_dir, wine_image)
        wine_image_output = os.path.join(self.images_dir, new_image_name)

        shutil.copy(wine_image_path, wine_image_output)

        return wine_image_output, datapoint_id

    def do_processing(self, image_path):

        prompt_opening_ovis = self.get_prompt("Wine feature extraction preamble OVIS")
        prompt_ocr = self.get_prompt("Wine Extraction OCR")
        prompt_closing_ovis = self.get_prompt("Wine feature extraction closing OVIS")

        image_features = self.get_image_prompts("wine")

        ocr_extract = self.ocr(image_path)

        string_features = []

        for image_feature in image_features:
            string_features.append(f"{{feature: \"{image_feature[0]}\", json_name: \"{image_feature[1]}\"}}")

        prompt = f"""
                          {prompt_opening_ovis} \n
                          [ \n
                          {",\n".join(string_features)} \n
                          ] \n
                          {prompt_ocr} \n
                          [{ocr_extract}] The OCR extract is complete. \n
                          {prompt_closing_ovis}
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
