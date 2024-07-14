import logging
import sys
import threading
import time
from multiprocessing import Process
from typing import Optional

import pyautogui
from pynput import keyboard

from action import BaseAction, FightAction, ActionSequenceParser, FightRes
from error import UnexpectedUI, UserInterrupt, ConfigError, ReturnMainUIFail, GlobalVar
from utils import get_config, init_game_window, set_logger, screenshot

logger = logging.getLogger(__name__)


class Main:
    def __init__(self):
        self.config = get_config()
        self.action: Optional[BaseAction] = None
        self.fight: Optional[FightAction] = None

    def main(self):
        try:
            self.prepare()
            self.process()
        except UserInterrupt as e:
            logger.info(f"用户终止了程序")
            logger.debug(f"{e}", exc_info=True)
            for key in ["w", "a", "s", "d", "alt"]:
                pyautogui.keyUp(key)
        except ConfigError as e:
            logger.error(f"配置文件有误，请检查！{e.message}")
            logger.debug(f"{e}", exc_info=True)
        except ReturnMainUIFail as e:
            logger.error(f"返回到主界面失败")
            logger.debug(f"{e}", exc_info=True)
            screenshot()
        except Exception as e:
            logger.error(f"出现了未知错误：{e}")
            logger.debug(f"{e}", exc_info=True)
            screenshot()

    def process(self):
        epoch = 1
        task_index = 0
        echo_num = 0
        task_retry_times = 0
        task_retry_times_max = 3
        retry_task = False

        start_time = time.time()
        logger.info(f"任务：{self.config['tasks']}")
        task_list = self.config["tasks"].split(",")
        while True:
            task = task_list[task_index]
            used_time = int((time.time() - start_time) / 60)
            progress = f"第 {epoch} 轮，当前任务：{task}，已吸收声骸：{echo_num}，已执行 {used_time} 分钟"
            logger.debug(progress)
            if not retry_task:
                print(f"\033[1;32;40m{progress}\033[0m")

            try:
                self.action.try_return_main_ui(30)
                if self.action.afterimage_explore(task):
                    self.action.teleport_to_afterimage(task)
                    parser = ActionSequenceParser()
                    fight_loop = parser.parse(self.config["fight_loop"])
                    fight_res = self.fight.execute_fight(fight_loop)
                    if fight_res == FightRes.OK:
                        if self.action.absorb_echo():
                            echo_num += 1
                        for key in ["w", "a", "s", "d", "alt"]:
                            pyautogui.keyUp(key)
                        retry_task = False
                    elif fight_res == FightRes.DIED:
                        self.action.try_return_main_ui(10)
                        self.action.goto_core_beacon()
                        retry_task = True
                    elif fight_res == FightRes.TIMEOUT:
                        self.action.try_return_main_ui(10)
                        retry_task = False
                    else:
                        raise ValueError(f"异常的FightRes: {fight_res}")
                else:
                    logger.warning(f"没有找到任务：{task}，重试中")
                    retry_task = True
            except UnexpectedUI as e:
                logger.error(f"遇到了非预期界面，尝试返回主界面。预期界面：{e.expect}")
                logger.debug(f"{e}", exc_info=True)
                screenshot()
                retry_task = True

            if retry_task:
                # 重试任务
                task_retry_times += 1
                self.action.try_return_main_ui(30)
                if task_retry_times > task_retry_times_max:
                    task_index = (task_index + 1) % len(task_list)
                    epoch += task_index == 0
                    task_retry_times = 0
            else:
                # 如果血量不健康就回血
                self.action.goto_core_beacon_if_not_health()
                # 切到下一个任务
                task_index = (task_index + 1) % len(task_list)
                epoch += task_index == 0

    def prepare(self):
        set_logger()
        init_game_window()
        shortcut_thread = threading.Thread(target=listen_for_shortcut)
        shortcut_thread.daemon = True
        shortcut_thread.start()
        self.action = BaseAction()
        self.fight = FightAction()


def listen_for_shortcut():
    def on_activate():
        GlobalVar.stop_main = True

    with keyboard.GlobalHotKeys({"<alt>+<f5>": on_activate}) as hotkey:
        hotkey.join()


if __name__ == '__main__':
    Main().main()
