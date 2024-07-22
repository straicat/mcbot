from utils import get_config

preset = get_config().get("preset", "win_2560_1440")


class Region:
    if preset == "win_2560_1440":
        # 右下角文字：特征码
        feat_code = [2280, 1455, 2358, 1482]

        # 技能按键提示
        e_skill_key = [2133, 1395, 2147, 1415]
        q_skill_key = [2273, 1395, 2291, 1416]
        r_skill_key = [2418, 1397, 2430, 1415]

        # 背包图标
        bag_icon = [414, 81, 480, 150]

        # 地图文字：自定义标记
        map_custom_tag = [2234, 1361, 2405, 1394]

        # 索拉指南标题文字
        sora_guide_title = [150, 113, 297, 156]
        afterimage_explore_icon = [78, 99, 141, 170]

        # 终端文字：生日
        terminal_birthday = [164, 921, 228, 956]

        # 残象探寻 boss 列表文字区域
        boss_text_list = [407, 210, 576, 1242]

        # 点击探测后再点击 boss 位置，弹出 boss 和借位信标的选项，借位信标可能在这2个位置出现
        proxy_beacon_option1 = [1761, 774, 1905, 812]  # 第1个选项
        proxy_beacon_option2 = [1761, 887, 1905, 924]  # 第2个选项

        # 点击借位信标后文字：快速旅行
        proxy_beacon_recycle = [1907, 1365, 1976, 1401]
        proxy_beacon_fast_travel = [2273, 1365, 2412, 1401]

        # 点击小型信标或中枢信标后文字：快速旅行
        core_beacon_fast_travel = [2061, 1362, 2217, 1404]

        # 战斗时，左侧显示的“击败”文字。注意：如果有任务，左侧的击败会下移。这个数值是没有任务时的。
        boss_defeat_text = [94, 405, 168, 444]

        # 吸收声骸选项位置可能有3种
        absorb_option0 = [1803, 771, 1860, 801]  # 只有吸收选项
        absorb_option1 = [1803, 711, 1860, 743]  # 第1个选项是吸收，第2个选项是领取奖励
        absorb_option2 = [1803, 801, 1860, 831]  # 第2个选项是吸收，第1个选项是领取奖励

        # 在吸收/领取奖励时，F键图标出现范围
        f_absorb_key = [1664, 714, 1701, 839]
        # F键指示的选项列表中前2个文字的范围
        f_absorb_options_text = [1803, 714, 1860, 831]

        # 在副本门口，F键图标出现范围
        f_dungeon_key = [1665, 771, 1697, 806]

        # 存在领取奖励与吸收选项时，f键位置可能有2种
        f_select_key1 = [1676, 720, 1688, 740]  # 第1个选项位置
        f_select_key2 = [1676, 809, 1688, 831]  # 第2个选项位置

        # 角色切换按键 1 2 3
        role_1_key = [2331, 332, 2339, 348]
        role_2_key = [2330, 506, 2343, 525]
        role_3_key = [2331, 683, 2342, 701]

        # 点击中枢信标后弹出的面板上方的“中枢信标”文字
        core_beacon_panel = [1893, 107, 2078, 153]

        # 复苏弹窗标题：选择复苏物品
        revival_popup_title = [491, 311, 722, 351]

        # 领取奖励弹窗标题的“领”字
        get_reward_popup_title = [600, 504, 642, 546]
        # 补充结晶波片弹窗标题的“补”字
        supply_vigor_popup_title = [492, 315, 530, 353]

        # 副本选择等级界面，推荐等级前小图片搜索范围
        dungeon_level_icon_search = [186, 258, 270, 459]

        # 副本确认离开
        dungeon_confirm_exit_text = [1202, 717, 1358, 756]


class Position:
    if preset == "win_2560_1440":
        # 索拉指南残象探寻点击位置
        afterimage_explore = [111, 816]

        # 残象列表空白位置
        afterimage_list_blank = [945, 717]

        # 残像探寻探测按钮
        explore_btn = [2285, 1362]

        # 点击探测后在地图上残象 boss 的位置
        boss_map_explore = [1290, 770]

        # 地图右上角逆境深塔进度
        tower_status = [1745, 128]
        # 点击逆境深塔后，点击中枢信标位置
        core_beacon_when_tower_panel = [954, 660]

        # 游戏界面边缘安全的空白点击位置
        blank_click = [2550, 63]

        # TBD: 后续改为OCR
        # 进入副本时单人挑战按钮，以及编队界面的开启挑战
        dungeon_challenge_btn = [2262, 1356]
        # 进入副本时提示结晶波片不足，确认进入
        dungeon_popup_confirm = [1653, 942]


class Range:
    if preset == "win_2560_1440":
        # F键图标出现时，其中心点y值范围。以下分别代表F键是唯一选项、第1个选项、第2个选项时的y值范围。
        f_select_key_y0 = [779, 799]
        f_select_key_y1 = [721, 741]
        f_select_key_y2 = [810, 830]


class PosColor:
    if preset == "win_2560_1440":
        # 判断角色不健康的位置与颜色 RGB
        role1_not_health = [[2385, 430], [75, 75, 75]]
        role2_not_health = [[2385, 606], [75, 75, 75]]
        role3_not_health = [[2385, 782], [75, 75, 75]]

        # 通过BOSS血条初步判断仍然存活
        boss_hp_bar = [[950, 128], [255, 179, 68]]
        # BOSS存活时，左侧会有击败BOSS的任务，从任务图标上取点
        # 注意：当有其它任务时，击败BOSS的任务会在下面的位置
        defeat_boss_icon1 = [[54, 450], [148, 140, 244]]
        defeat_boss_icon2 = [[54, 648], [148, 140, 244]]

        # 战歌重奏命定的纷争，各推荐等级选中时的取点与颜色
        dungeon_level40 = [[500, 300], [227, 227, 227]]
        dungeon_level50 = [[500, 411], [227, 227, 227]]
        dungeon_level60 = [[500, 524], [227, 227, 227]]
        dungeon_level70 = [[500, 635], [227, 227, 227]]
        dungeon_level80 = [[500, 747], [227, 227, 227]]
        dungeon_level90 = [[500, 858], [227, 227, 227]]


if __name__ == '__main__':
    print(Region.feat_code)
