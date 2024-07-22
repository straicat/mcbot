import configparser
import ctypes
import functools
import inspect
import logging
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import pyautogui
import win32con
import win32gui
from PIL import ImageGrab

from error import ConfigError, GlobalVar, UserInterrupt

logger = logging.getLogger(__name__)


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


def log_exec(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        exec_time = time.time() - start_time
        caller = inspect.stack()[1].function
        logger.debug(f"{caller}.{func.__name__} return:{result}, time:{exec_time}s")
        return result

    return wrapper


def set_logger(file_handler_level=logging.DEBUG, stream_handler_level=logging.INFO):
    root = logging.getLogger()
    for handler in root.handlers:
        root.removeHandler(handler)
    root.setLevel(logging.DEBUG)
    debug_formatter = logging.Formatter("%(asctime)s %(levelname)s %(filename)s:%(lineno)d#%(funcName)s %(message)s")
    other_formatter = logging.Formatter("%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    if file_handler_level:
        log = os.path.join(os.path.dirname(__file__), os.pardir, "data", "logs", f"log-{datetime.now().strftime('%Y-%m-%d')}.txt")
        os.makedirs(os.path.dirname(log), exist_ok=True)
        fh = logging.FileHandler(log, encoding="utf-8")
        fh.setLevel(file_handler_level)
        if fh.level == logging.DEBUG:
            fh.setFormatter(debug_formatter)
        else:
            fh.setFormatter(other_formatter)
        fh.setFormatter(debug_formatter)
        root.addHandler(fh)
    if stream_handler_level:
        sh = logging.StreamHandler(stream=sys.stdout)
        sh.setLevel(stream_handler_level)
        if sh.level == logging.DEBUG:
            sh.setFormatter(debug_formatter)
        else:
            sh.setFormatter(other_formatter)
        root.addHandler(sh)


def get_config():
    ini_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "data", "config.ini"))
    section = "General"
    if not os.path.isfile(ini_path):
        raise ConfigError(f"配置文件不存在：{ini_path}")
    parser = configparser.ConfigParser()
    for enc in ("utf-8", "gb18030", "gb2312", "gbk", "utf_8_sig"):
        try:
            parser.read(ini_path, encoding=enc)
            break
        except (UnicodeDecodeError, configparser.MissingSectionHeaderError):
            continue
    if section not in parser:
        raise ConfigError(f"配置文件解析失败：{ini_path}")
    return dict(parser[section])


def sleep(secs, rand=0.05):
    if GlobalVar.stop_main:
        raise UserInterrupt()
    wait_time = secs + random.uniform(-rand, rand)
    time.sleep(wait_time)
    return wait_time


def click(position, rand=(10, 10)):
    real_pos = [int(position[0] + random.uniform(-rand[0], rand[0])), int(position[1] + random.uniform(-rand[1], rand[1]))]
    pyautogui.click(real_pos)


def region_center(region):
    assert len(region) == 4
    return [int((region[0] + region[2]) / 2), int((region[1] + region[3]) / 2)]


def is_subsequence(target, source):
    i = j = 0
    while i < len(target) and j < len(source):
        if target[i] == source[j]:
            i += 1
        j += 1
    return i == len(target)


def init_game_window():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        raise RuntimeError("脚本需要以管理员权限运行")

    hwnd = win32gui.FindWindow("UnrealWindow", "鸣潮  ")
    if not hwnd:
        raise RuntimeError("无法找到鸣潮游戏的窗口")
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOSIZE)


def screenshot():
    img_path = Path(__file__).parent.parent / "data/screenshots" / datetime.now().strftime("%Y%m%d-%H%M%S-%f.png")
    img_path.parent.mkdir(parents=True, exist_ok=True)
    im = ImageGrab.grab()
    im.save(img_path)
    logger.debug(f"save screenshot: {img_path}")


def test():
    pass


if __name__ == '__main__':
    test()
