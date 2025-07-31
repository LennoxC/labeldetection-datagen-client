import os
import gzip
import random
import urllib.request
from datasets.loader import Loader
import os

class FoodLoader(Loader):
    def __init__(self, data_location):
        super(FoodLoader, self).__init__("food")

        '''
        self.data_location = data_location # this is /food in the data root
        self.images_dir = os.path.join(data_location, "images") # /food/images
        self.ocr_dir = os.path.join(data_location, "ocr") # /food/ocr
        self.metadata_dir = os.path.join(data_location, "metadata")

        # specific to food dataset AWS download
        self.bucket_url = "https://openfoodfacts-images.s3.eu-west-3.amazonaws.com/"
        data_keys_url = self.bucket_url + "data/data_keys.gz"
        self.local_keys_file = f"{self.metadata_dir}/data_keys.gz"

        self.logger.debug("Init Food Loader")

        if not os.path.exists(data_location):
            os.makedirs(data_location)

        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.ocr_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)

        if not os.path.exists(self.local_keys_file):
            self.logger.info("Downloading data keys file.")
            print(f"Downloading {data_keys_url}...")
            urllib.request.urlretrieve(data_keys_url, self.local_keys_file)
        '''

    # load an image
    def load(self):
        self.download()

    # sample some prompts
    def prompts(self):
        pass

    # package to a query
    def package(self):
        pass

    # --------------- non inherited methods (custom application specific logic) ---------------

    def download(self):
        self.logger.debug("Sampling a random food image.")
        with gzip.open(self.local_keys_file, 'rt') as f:
            all_keys = [line.strip() for line in f]

        sampled_keys = random.sample(all_keys, 1)

        for key in sampled_keys:

            self.logger.debug(f"Downloading food image {key}")

            image_url = self.bucket_url + key
            datapoint_id = key.replace('data/', '').replace('/', '_').replace('.jpg', '')
            image_path = os.path.join(self.images_dir, f"{datapoint_id}.jpg")

            try:
                self.logger.debug(f"Downloading image: {image_url} -> {image_path}")
                urllib.request.urlretrieve(image_url, image_path)
            except Exception as e:
                self.logger.critical(f"Failed to download image {image_url}: {e}")