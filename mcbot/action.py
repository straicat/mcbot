from __future__ import annotations

import logging
import random
import re
import time
from dataclasses import dataclass
from enum import Enum
from pprint import pprint
from typing import Optional, List

import pyautogui
import win32api
import win32con

from error import UnexpectedUI, ReturnMainUIFail, ConfigError
from scene import Scene
from smart import Smart
from utils import sleep, click, region_center, is_subsequence, log_exec
from values import Region, Position

logger = logging.getLogger(__name__)


class BaseAction:
    def __init__(self):
        self.scene = Scene()
        self.smart = Smart()

    def try_return_main_ui(self, timeout):
        start = time.time()
        if self.scene.is_main_ui():
            return True
        logger.info("尝试回到主界面")
        while True:
            if time.time() - start > timeout:
                raise ReturnMainUIFail()
            if random.randint(0, 9) % 2 == 0:
                pyautogui.press("esc")
            else:
                click(Position.blank_click)
            sleep(0.5)
            if self.scene.is_main_ui():
                return True

    def wait_for_main_ui(self, interval, timeout):
        start = time.time()
        while True:
            if self.scene.is_main_ui():
                return True
            sleep(interval, 0)
            if time.time() - start > timeout:
                return False

    def goto_core_beacon(self):
        pyautogui.press("m")
        sleep(1.5)
        click(Position.tower_status)
        sleep(1.5)
        click(Position.core_beacon_when_tower_panel)
        sleep(1)
        click(region_center(Region.core_beacon_fast_travel))
        self.wait_for_main_ui(2, 15)
        sleep(1)

    def goto_core_beacon_if_not_health(self):
        if self.scene.is_role_not_health():
            self.goto_core_beacon()

    def afterimage_explore(self, task: str):
        logger.info(f"残象探寻：{task}")
        sleep(0.5)
        pyautogui.press("f2")
        sleep(0.8)
        click(Position.afterimage_explore)
        sleep(1)
        if not self.scene.is_afterimage_explore_ui():
            raise UnexpectedUI(expect="残象探寻")

        rare_chars = ["鸷", "鳞"]
        task_remap = {"辉萤军势": ["辉带军热"]}

        for _ in range(3):
            # TBD: 单拎出来测试识别效果
            boss_res = self.smart.ocr_region(Region.boss_text_list)
            for boss_r in boss_res:
                found = False
                if boss_r.text in task:
                    found = True
                elif task in task_remap:
                    for alias in task_remap[task]:
                        if is_subsequence(alias, boss_r.text):
                            found = True
                            break
                else:
                    for rare_char in rare_chars:
                        alias = task.replace(rare_char, "")
                        if is_subsequence(alias, boss_r.text):
                            found = True
                            break

                if found:
                    click(region_center(boss_r.region))
                    sleep(0.5)
                    return True

            pyautogui.moveTo(*Position.afterimage_list_blank, duration=0.2)
            pyautogui.scroll(-1500)
            sleep(1)
        return False

    def teleport_to_afterimage(self, task):
        """传送到残象位置，需要先在残象探寻界面选中要传送的残象，并且已在该残象附近放置借位信标
        """
        logger.info(f"传送至Boss：{task}")
        click(Position.explore_btn)
        sleep(2.5)
        click(Position.boss_map_explore)
        sleep(0.8)
        if self.smart.is_region_text(Region.proxy_beacon_option2, "借位信标"):
            click(region_center(Region.proxy_beacon_option2))
        elif self.smart.is_region_text(Region.proxy_beacon_option1, "借位信标"):
            click(region_center(Region.proxy_beacon_option1))
        else:
            raise UnexpectedUI(expect="借位信标选项")
        sleep(0.8)
        if not self.scene.is_proxy_beacon_panel():
            raise UnexpectedUI(expect="借位信标面板")
        click(region_center(Region.proxy_beacon_fast_travel))
        self.wait_for_main_ui(1, 15)
        if task == "鸣钟之龟":
            sleep(8)
        else:
            sleep(1)

    @log_exec
    def absorb_echo(self):
        start_time = time.time()
        logger.info("开始寻找声骸")
        span = 0
        cnt = 0
        while True:
            for direction in ["w", "d", "s", "a"]:
                if cnt % 2 == 0:
                    span += 1
                cnt += 1
                if span >= 4:
                    logger.debug(f"寻找声骸耗时：{time.time() - start_time}s，结果：未找到")
                    logger.info("没有找到声骸")
                    return False
                logger.debug(f"寻找声骸 跨度：{span}, 方向：{direction}")
                pyautogui.keyDown(direction)
                for _j in range(span * 3):  # TBD: 采用超时判断，而不是固定时延，控制更精确
                    if self.try_absorb(direction):
                        logger.debug(f"寻找声骸耗时：{time.time() - start_time}s，结果：已找到")
                        logger.info("已吸收声骸")
                        sleep(3.5)
                        return True
                    pyautogui.keyDown(direction)
                    sleep(0.1, 0)
                pyautogui.keyUp(direction)

    def try_absorb(self, key):
        f_key = self.scene.find_f_select_key()
        if f_key:
            if key:
                pyautogui.keyUp(key)
            # 等待奔跑惯性
            sleep(0.5)
            region = self.scene.get_absorb_option_region()
            if region:
                pyautogui.keyDown("alt")
                pyautogui.moveTo(*region_center(region), duration=0.1)
                # 鼠标划过选项时，选项高亮切换动画
                sleep(0.5)
                pyautogui.click()
                pyautogui.keyUp("alt")

                # 这里误触发弹窗的问题需要多测测
                if self.scene.use_vigor_popup():
                    logger.debug("吸收声骸失误触发体力弹窗")
                    pyautogui.keyUp("alt")
                    pyautogui.press("esc")
                    sleep(0.8)
                    return False
                return True
        return False


class FightRes(Enum):
    NOT_OVER = 0
    OK = 1
    DIED = 2
    TIMEOUT = 3


class FightAction(BaseAction):
    def __init__(self):
        super().__init__()
        self.min_fight_duration = 3
        # 最长战斗时间 单位：秒
        self.max_fight_duration = 300

    @log_exec
    def execute_fight(self, fight_loop):
        start_time = time.time()
        logger.info("开始战斗")
        boss_defeated = False
        fight_res = FightRes.NOT_OVER

        def execute_action_list(action_list):
            nonlocal boss_defeated
            nonlocal fight_res
            for action in action_list:
                if boss_defeated:
                    return
                if time.time() - start_time > self.max_fight_duration:
                    fight_res = FightRes.TIMEOUT
                    logger.info(f"战斗已超时，时限：{self.max_fight_duration}s")
                    return
                logger.debug(f"current action: {action}")
                if time.time() - start_time > self.min_fight_duration and self.scene.is_boss_defeated():
                    if self.scene.is_boss_defeated():  # 双重检测
                        boss_defeated = True
                        fight_res = FightRes.OK
                        logger.info("检测到已击败Boss，停止战斗")
                        return

                op = action.op
                down = action.down
                wait = action.wait
                post = action.post
                if op == "a":
                    pyautogui.mouseDown()
                    sleep(down / 1000, 0)
                    pyautogui.mouseUp()
                    sleep(wait / 1000, 0)
                elif op == "s":
                    pyautogui.keyDown("space")
                    sleep(down / 1000, 0)
                    pyautogui.keyUp("space")
                    sleep(wait / 1000, 0)
                elif op == "ls":
                    win32api.keybd_event(win32con.VK_LSHIFT, 0, 0, 0)
                    sleep(down / 1000, 0)
                    win32api.keybd_event(win32con.VK_LSHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
                    sleep(wait / 1000, 0)
                elif op in ["1", "2", "3"]:
                    pyautogui.keyDown(op)
                    sleep(down / 1000, 0)
                    pyautogui.keyUp(op)
                    sleep(wait / 1000, 0)
                    # 关闭死亡弹窗
                    if self.scene.is_revival_popup():
                        pyautogui.press("esc")
                        sleep(0.5)
                        fight_res = FightRes.DIED
                        return
                else:
                    pyautogui.keyDown(op)
                    sleep(down / 1000, 0)
                    pyautogui.keyUp(op)
                    sleep(wait / 1000, 0)
                if post:
                    if not self.scene.is_main_ui():
                        self.wait_for_main_ui(0.2, 3)
                        execute_action_list(post)

        pyautogui.click(button='middle')
        while True:
            execute_action_list(fight_loop)
            if fight_res != FightRes.NOT_OVER:
                logger.debug(f"战斗耗时：{time.time() - start_time}s")
                return fight_res


class ActionSequenceParser:
    def __init__(self):
        self.all_ops = ["a", "q", "e", "r", "t", "s", "ls", "1", "2", "3"]
        self.float_pattern = re.compile(r'\d*\.\d+|\d+')
        self.config_pattern = re.compile(r'\[(.*?)]')
        self.default_config = {}
        for op in self.all_ops:
            self.default_config[op] = {"down": 100, "wait": 20}

    def parse(self, dsl):
        return self._parse(dsl, 0, len(dsl), self.default_config)[0]

    def _parse(self, dsl, st, ed, config):
        res = []
        while st < ed:
            if dsl[st] == '[':
                config, st = self._parse_config(dsl, st, config)
            elif dsl[st] in (' ', ';'):
                st += 1
            else:
                action, st = self._parse_action(dsl, st, ed, config)
                res.append(action)
        return res, ed + 1

    def _parse_time(self, t):
        if not re.fullmatch(self.float_pattern, t):
            raise ValueError(t)
        if '.' in t:
            return int(float(t) * 1000)
        return int(t) * 1000

    def _parse_config(self, dsl, st, config):
        res = {}
        match = self.config_pattern.match(dsl[st:])
        if match:
            for conf in re.split(r';| +', match.group(1)):
                if not conf:
                    continue
                if ":" in conf:
                    ops, times = conf.split(":")
                    down, wait = times.split(",")
                    for op in ops.split(","):
                        res[op] = {"down": self._parse_time(down), "wait": self._parse_time(wait), }
                else:
                    down, wait = conf.split(",")
                    for op in self.all_ops:
                        if op not in res:
                            res[op] = {"down": self._parse_time(down), "wait": self._parse_time(wait)}
        config.update(res)
        return config, st + match.end()

    def _parse_action(self, dsl, st, ed, config):
        p = st
        for op in self.all_ops:
            if not (op[0] == dsl[st] and (len(op) == 1 or (st + 1 < ed and op[1] == dsl[st + 1]))):
                continue
            p += len(op)
            down = config[op]["down"]
            wait = config[op]["wait"]
            if p == ed or dsl[p] in (' ', ';', '['):
                return Action(op, down, wait), p
            elif dsl[p] not in (',', '{'):
                break
            q = p
            if dsl[p] == ',':
                q = p + 1
                while q < ed:
                    if dsl[q] in (',', ' ', ';', '['):
                        break
                    elif not str.isdigit(dsl[q]) and dsl[q] != '.':
                        raise ConfigError(f"动作序列解析错误，位置：{q}")
                    else:
                        q += 1
                if down_str := dsl[p + 1:q]:
                    down = self._parse_time(down_str)
                if q == ed or dsl[q] in (' ', ';', '['):
                    return Action(op, down, wait), q
                p = q
                q = p + 1
                while q < ed:
                    if dsl[q] in (' ', ';', '[', '{'):
                        break
                    elif not str.isdigit(dsl[q]) and dsl[q] != '.':
                        raise ConfigError(f"动作序列解析错误，位置：{q}")
                    else:
                        q += 1
                if wait_str := dsl[p + 1:q]:
                    wait = self._parse_time(wait_str)
            if q < ed and dsl[q] == '{':
                try:
                    r = self._get_match_bracket(dsl, q)
                except ValueError:
                    raise ConfigError(f"动作序列解析错误，位置：{q}")
                post, p = self._parse(dsl, q + 1, r, config)
                return Action(op, down, wait, post), p + 1
            return Action(op, down, wait), q
        raise ConfigError(f"动作序列解析错误，位置：{p}")

    @staticmethod
    def _get_match_bracket(string, left):
        stk = ['{']
        for i in range(left + 1, len(string)):
            if string[i] == '{':
                stk.append('{')
            elif string[i] == '}':
                if not stk:
                    raise ValueError
                stk.pop()
                if not stk:
                    return i
        if stk:
            raise ValueError


@dataclass
class Action:
    op: str
    down: int = 0
    wait: int = 0
    post: Optional[List[Action]] = None


def test():
    dsl = "[a:.05,.1;q,e,r:.05,.3;1,2,3:.05,.05;.1,.2]1;e 3;e 2;e 1;a;a;a;a[a:.02,.03]e;e a;a;a;a e{} r{[a:.02,.05]a;a;e;a;a;a;a}"
    res = ActionSequenceParser().parse(dsl)
    pprint(res)


if __name__ == '__main__':
    test()
