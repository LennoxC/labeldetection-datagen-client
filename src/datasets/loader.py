from abc import ABC, abstractmethod
import logging

class Loader:
    def __init__(self, dataset):
        self.dataset = dataset
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

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
