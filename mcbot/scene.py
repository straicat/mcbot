import functools
import logging
from pathlib import Path

import numpy as np
from PIL import ImageGrab, Image

from smart import Smart
from utils import singleton, get_config, log_exec, set_logger
from values import Region, PosColor

logger = logging.getLogger(__name__)


@singleton
class Scene:
    def __init__(self):
        self.smart = Smart()
        self.res_path = Path(__file__).parent / "res" / get_config().get("preset", "win_2560_1440")
        self.task = ""

    @functools.lru_cache
    def _res(self, name):
        image = Image.open(self.res_path / name)
        data = np.array(image)
        image.close()
        return data

    @log_exec
    def is_main_ui(self):
        return self.smart.find_region_image(Region.bag_icon, self._res("背包.png"))

    @log_exec
    def is_afterimage_explore_ui(self):
        return self.smart.is_region_text(Region.sora_guide_title, "残象探寻")

    @log_exec
    def is_proxy_beacon_panel(self):
        return self.smart.is_region_text(Region.proxy_beacon_fast_travel, "快速旅行")

    @log_exec
    def is_boss_defeated(self):
        # BOSS血条不为空
        if self.smart.is_pos_color(PosColor.boss_hp_bar):
            return False
        # 不是主界面，说明应该是在播放大招动画，此时视为未击败
        if not self.is_main_ui():
            return False
        # 最后再检查下击败BOSS任务图标
        if self.task in ["角", "无冠者"]:
            return self.smart.is_region_text(Region.dungeon_exit_text, "离开")
        else:
            if self.smart.is_pos_color(PosColor.defeat_boss_icon1) or self.smart.is_pos_color(PosColor.defeat_boss_icon2):
                return False
        return True

    @log_exec
    def with_feat_code(self):
        return self.smart.is_region_text(Region.feat_code, "特征码")

    @log_exec
    def is_revival_popup(self):  # TBD: 太慢了，待优化。先检查颜色快速判断
        return self.smart.is_region_text(Region.revival_popup_title, "选择复苏物品")

    @log_exec
    def find_f_absorb_key(self):
        return self.smart.find_region_image(Region.f_absorb_key, self._res("F键.png"))

    @log_exec
    def find_f_dungeon_key(self):
        return self.smart.find_region_image(Region.f_dungeon_key, self._res("F键.png"))

    @log_exec
    def get_absorb_option_region(self):
        for ret in self.smart.ocr_region(Region.f_absorb_options_text):
            if ret.text == "吸收" and ret.score >= 0.9:
                return ret.region

    @log_exec
    def use_vigor_popup(self):
        # 补充结晶波片
        if self.smart.is_region_text(Region.supply_vigor_popup_title, "补"):
            return True
        # 领取奖励需要消耗结晶波片
        if self.smart.is_region_text(Region.get_reward_popup_title, "领"):
            return True
        return False

    @log_exec
    def is_role_not_health(self):
        tolerance = 20
        if self.smart.is_pos_color(PosColor.role1_not_health, tolerance):
            return True
        if self.smart.is_pos_color(PosColor.role2_not_health, tolerance):
            return True
        if self.smart.is_pos_color(PosColor.role3_not_health, tolerance):
            return True
        return False

    def is_dungeon_level_select_ui(self):
        return bool(self.smart.find_region_image(Region.dungeon_level_icon_search, self._res("副本等级.png")))

    def get_proper_dungeon_level_position(self):
        levels = [PosColor.dungeon_level90, PosColor.dungeon_level80, PosColor.dungeon_level70, PosColor.dungeon_level60, PosColor.dungeon_level50, PosColor.dungeon_level40]
        proper = [PosColor.dungeon_level70, PosColor.dungeon_level60, PosColor.dungeon_level50, PosColor.dungeon_level40, PosColor.dungeon_level40, PosColor.dungeon_level40]
        for i, level in enumerate(levels):
            if self.smart.is_pos_color(level):
                return proper[i][0]

    def is_dungeon_confirm_exit(self):
        return self.smart.is_region_text(Region.dungeon_confirm_exit_text, "确认离开")


def test():
    test_image = r"D:\Pictures\鸣潮\角\20240722-131343-762136.png"

    def mock_grab(region):
        im = Image.open(test_image)
        res = im.crop(region)
        im.close()
        return res

    set_logger(0, logging.DEBUG)
    s = Scene()
    s.task = "无冠者"
    for _ in range(3):
        ImageGrab.grab = mock_grab
        logger.info(s.is_boss_defeated())


if __name__ == '__main__':
    test()
