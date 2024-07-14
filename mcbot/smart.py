import logging
import time
from dataclasses import dataclass
from typing import List, Optional

import cv2
import numpy as np
import paddle
import pyautogui
from PIL import ImageGrab
from paddleocr import PaddleOCR

from utils import singleton

logger = logging.getLogger(__name__)


@dataclass
class OcrRet:
    text: str
    region: List[int]
    score: float


@singleton
class Smart:
    def __init__(self):
        self.__ocr: Optional[PaddleOCR] = None

    @property
    def _ocr(self):
        if self.__ocr is None:
            start = time.time()
            logger.info("正在加载PaddleOCR，请稍等...")
            use_gpu = paddle.is_compiled_with_cuda() and paddle.get_device().startswith("gpu")
            self.__ocr: Optional[PaddleOCR] = None
            self.__ocr = PaddleOCR(use_angle_cls=False, use_gpu=use_gpu, lang="ch", precision="int8", show_log=False)
            logging.getLogger("ppocr").setLevel(logging.ERROR)
            logger.debug(f"paddle ocr loaded. use_gpu:{use_gpu}, time:{time.time() - start}s")
        return self.__ocr

    def ocr_region(self, region: List[int]) -> List[OcrRet]:
        assert len(region) == 4
        start = time.time()
        image = ImageGrab.grab(region)
        rets = self._ocr.ocr(np.array(image))
        logger.debug(f"ocr_region region:{region}, rets:{rets}, time:{time.time() - start}s")
        res = []
        for ret in rets:
            if not ret:
                continue
            for line in ret:
                box = line[0]
                x1 = int(box[0][0] + region[0])
                y1 = int(box[0][1] + region[1])
                x2 = int(box[2][0] + region[0])
                y2 = int(box[2][1] + region[1])
                res.append(OcrRet(text=line[1][0], region=[x1, y1, x2, y2], score=line[1][1]))
        return res

    def is_region_text(self, region: List[int], text: str, confidence=0.9) -> bool:
        assert len(region) == 4
        start = time.time()
        image = ImageGrab.grab(region)
        rets = self._ocr.ocr(np.array(image), det=False)
        logger.debug(f"is_region_text region:{region}, rets:{rets}, time:{time.time() - start}s")
        for ret in rets:
            for line in ret:
                if text in line[0] and line[1] >= confidence:
                    return True
        return False

    @staticmethod
    def find_region_image(region: List[int], templ: np.ndarray, confidence=0.9, gray=True) -> List[int]:
        assert len(region) == 4
        start = time.time()
        image = np.array(ImageGrab.grab(region))
        if gray:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            templ = cv2.cvtColor(templ, cv2.COLOR_RGB2GRAY)
        result = cv2.matchTemplate(image, templ, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        logger.debug(f"find_region_image region:{region}, shape:{templ.shape}, max_val:{max_val}, max_loc:{max_loc}, time:{time.time() - start}s")
        if max_val >= confidence:
            x1 = max_loc[0] + region[0]
            y1 = max_loc[1] + region[1]
            x2 = x1 + templ.shape[1]
            y2 = y1 + templ.shape[0]
            return [x1, y1, x2, y2]
        return []

    @staticmethod
    def is_pos_color(pos_color: List[List[int]], tolerance=10):
        # noinspection PyUnresolvedReferences
        return pyautogui.pixelMatchesColor(*pos_color[0], pos_color[1], tolerance=tolerance)
