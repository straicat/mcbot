import logging
import threading
import time
from typing import Optional

import pyautogui
from pynput import keyboard

from action import BaseAction, FightAction, ActionSequenceParser, FightRes, DungeonTaskAction, BeaconTaskAction
from error import UnexpectedUI, UserInterrupt, ConfigError, ReturnMainUIFail, GlobalVar
from utils import get_config, init_game_window, set_logger, screenshot

logger = logging.getLogger(__name__)


class Main:
    def __init__(self):
        self.config = get_config()
        self.action: Optional[BaseAction] = None
        self.fight: Optional[FightAction] = None
        self.task_list = []
        self.dungeon_boss_list = ["角", "无冠者"]

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
        span_limit, span_val = 4, 3

        parser = ActionSequenceParser()
        fight_loop = parser.parse(self.config.get("fight_loop", "1;r;e;q;a;a;a 2;r;e;q 3;r;e;q"))
        start_time = time.time()
        while True:
            task = self.task_list[task_index]
            self.action.set_task(task)
            used_time = int((time.time() - start_time) / 60)
            progress = f"第 {epoch} 轮，当前任务：{task}，已吸收声骸：{echo_num}，已执行 {used_time} 分钟"
            logger.debug(progress)
            if not retry_task:
                print(f"\033[1;32;40m{progress}\033[0m")

            try:
                fight_res = FightRes.NOT_OVER
                if task == "角":
                    span_limit, span_val = 6, 4
                elif task == "无冠者":
                    span_limit, span_val = 6, 3
                if isinstance(self.action, DungeonTaskAction):
                    if epoch == 1:
                        if not self.action.wait_for_level_select_ui(120):
                            continue
                    else:
                        self.action.auto_prepare_dungeon_ready()
                    if self.action.enter_dungeon():
                        fight_res = self.fight.execute_fight(fight_loop)
                    else:
                        logger.warning(f"进入副本 {task} 失败，重试中")
                        retry_task = True
                elif isinstance(self.action, BeaconTaskAction):
                    self.action.try_return_main_ui(30)
                    if self.action.afterimage_explore(task):
                        self.action.teleport_to_afterimage(task)
                        fight_res = self.fight.execute_fight(fight_loop)
                    else:
                        logger.warning(f"没有找到任务：{task}，重试中")
                        retry_task = True
                else:
                    raise ValueError(f"error action type: {type(self.action)}")

                if fight_res == FightRes.OK:
                    if self.action.absorb_echo(span_limit, span_val):
                        echo_num += 1
                    for key in ["w", "a", "s", "d", "alt"]:
                        pyautogui.keyUp(key)
                    retry_task = False
                    if isinstance(self.action, DungeonTaskAction):
                        self.action.exit_dungeon()
                elif fight_res == FightRes.DIED:
                    self.action.try_return_main_ui(10)
                    self.action.goto_core_beacon()
                    retry_task = True
                elif fight_res == FightRes.TIMEOUT:
                    self.action.try_return_main_ui(10)
                    retry_task = False
                elif fight_res == FightRes.NOT_OVER:
                    pass
                else:
                    raise ValueError(f"error fight_res: {fight_res}")
            except UnexpectedUI as e:
                # TBD 尝试返回主界面对于角不适用
                logger.error(f"遇到了非预期界面，尝试返回主界面。预期界面：{e.expect}")
                logger.debug(f"{e}", exc_info=True)
                screenshot()
                retry_task = True

            if retry_task:
                # 重试任务
                task_retry_times += 1
                self.action.try_return_main_ui(30)
                if task_retry_times > task_retry_times_max:
                    task_index = (task_index + 1) % len(self.task_list)
                    epoch += task_index == 0
                    task_retry_times = 0
            else:
                # 如果血量不健康就回血
                if task not in self.dungeon_boss_list:
                    self.action.goto_core_beacon_if_not_health()
                # 切到下一个任务
                task_index = (task_index + 1) % len(self.task_list)
                epoch += task_index == 0

    def prepare(self):
        set_logger()
        init_game_window()
        shortcut_thread = threading.Thread(target=listen_for_shortcut)
        shortcut_thread.daemon = True
        shortcut_thread.start()
        self.fight = FightAction()

        logger.info(f"任务：{self.config.get('tasks')}")
        self.task_list = self.config.get("tasks", "").split(",")
        if len(self.task_list) > 3:
            raise ConfigError("tasks最多可配置3个")
        elif not self.task_list:
            raise ConfigError("tasks未配置")
        if len(self.task_list) > 1:
            for dungeon_boss in self.dungeon_boss_list:
                if dungeon_boss in self.task_list:
                    raise ConfigError(f"{dungeon_boss} 不可与其余boss一起配置")

        if len(self.task_list) == 1 and self.task_list[0] in self.dungeon_boss_list:
            self.action = DungeonTaskAction()
        else:
            self.action = BeaconTaskAction()
        self.action.scene.with_feat_code()


def listen_for_shortcut():
    def on_activate():
        GlobalVar.stop_main = True

    with keyboard.GlobalHotKeys({"<alt>+<f5>": on_activate}) as hotkey:
        hotkey.join()


if __name__ == '__main__':
    Main().main()
