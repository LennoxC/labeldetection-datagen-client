from src.datasets.loader import Loader

class WineLoader(Loader):
    def __init__(self, data_location):
        self.dataset = "wine"
        self.data_location = data_location

    def load(self):
        # read from local files
        pass


