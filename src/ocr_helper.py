from paddleocr import PaddleOCR


class OCRHelper:
    def __init__(self):
        self.ocr = PaddleOCR(use_angle_cls=True)

    def inference(self, image_path):
        result = self.ocr.ocr(image_path)

        text_lines = result[0]['rec_texts']

        return text_lines