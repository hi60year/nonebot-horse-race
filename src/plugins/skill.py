import datetime
from abc import ABC, abstractmethod, abstractstaticmethod
import json
import random
from typing import Literal, Type, Union, List, Dict
from horse import Horse, get_tracks_str
from nonebot.adapters.cqhttp import GroupMessageEvent
from nonebot.adapters import Bot
import mysql.connector
from .score_system import User
from copy import deepcopy
from types import MethodType
import numpy as np
import asyncio

mysql_connect_config = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'calenderbot',
}

class Skill(ABC):
    desc: str = None
    name: str = None
    command: str = None
    level: str = None
    def __init__(self):
        self.last_used_time: datetime.datetime = None
        self.cd: datetime.timedelta = None

    def cd_remain(self) -> Union[datetime.timedelta, Literal[False]]:
        if self.last_used_time is None:
            return False
        elapsed = datetime.datetime.now() - self.last_used_time
        if elapsed < self.cd:
            return self.cd - elapsed
        else:
            return False

    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        pass

    def get_desc(self):
        return \
f"""
{self.name}
{self.level} 技能
{self.desc}
CD时长： {self.cd}
""".strip()

class PrimarySkill(Skill):
    level = "初阶"
    def __init__(self):
        super().__init__()
        self.cd = datetime.timedelta(hours = 1)

class IntermediateSkill(Skill):
    level = "中阶"
    def __init__(self):
        super().__init__()
        self.cd = datetime.timedelta(hours = 3)

class AdvancedSkill(Skill):
    level = "高阶"
    def __init__(self):
        super().__init__()
        self.cd = datetime.timedelta(days = 1)

class SkillFactory:
    primary_skill_list : List[Type[PrimarySkill]] = []
    intermediate_skill_list : List[Type[IntermediateSkill]] = []
    advanced_skill_list : List[Type[AdvancedSkill]] = []
    @classmethod
    def get_all_skill_list(cls) -> List[Type[Skill]]:
        return cls.primary_skill_list + cls.intermediate_skill_list + cls.advanced_skill_list
    @classmethod
    def get_skill_name_dict(cls):
        return {skill.command : skill for skill in cls.get_all_skill_list()}
    @classmethod
    def skill_serializer(cls, skill: Skill):
        if skill is None: return json.dumps(None)
        return json.dumps({
            'type' : skill.command,
            'last_used_time' : skill.last_used_time.isoformat() if skill.last_used_time is not None else None
        })
    @classmethod
    def skill_deserializer(cls, data: str):
        data: Dict = json.loads(data)
        if data is None:
            return None
        type = cls.get_skill_name_dict()[data['type']]
        res = type()
        res.last_used_time = datetime.datetime.fromisoformat(data['last_used_time']) if data['last_used_time'] is not None else None
        return res

class AgilityPromotion(PrimarySkill):
    name = "迅捷1级 - Agility Promotion Ⅰ"
    command = "迅捷"
    desc = \
        "使目标的基础速度提升1.00点\n"\
        "用法：迅捷 <目标>\n"\
        "例子：迅捷 2 | 使得2号马的基础速度提升1.00点"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        msg = \
            f"技能生效：{self.name}\n"\
            f"目标 {target}号马 基础速度提升1.00点。"
        await bot.send(event, msg)
        horse_list[target - 1].speed += 1.00
        self.last_used_time = datetime.datetime.now()
        
SkillFactory.primary_skill_list.append(AgilityPromotion)

class SpeedImmobilization(PrimarySkill):
    name = "定速1级 - Speed Immobilization Ⅰ"
    command = "定速"
    desc = \
"""
免除目标的不稳定性
用法：定速 <目标>
例子：定速 3 | 使3号马的不稳定性降为0.0000
""".strip()
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        msg = \
f"""
技能生效：{self.name}
目标 {target}号马 不稳定性降至 0.0000。
""".strip()
        await bot.send(event, msg)
        horse_list[target - 1].stability = 0.0000
        self.last_used_time = datetime.datetime.now()

SkillFactory.primary_skill_list.append(SpeedImmobilization)

class Interference(PrimarySkill):
    name = "干扰1级 - Interference Ⅰ"
    command = "干扰"
    desc = \
"""
使一个目标的不稳定性提高3.0000点，但是最高不会超过7.0000
用法：干扰 <目标>
例子：干扰 4 | 使4号马的不稳定性提高3.0000
""".strip()
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        msg = \
f"""
技能生效：{self.name}
目标 {target}号马 不稳定性提高3.0000
""".strip()
        await bot.send(event, msg)
        horse_list[target - 1].stability += 3.0000
        self.last_used_time = datetime.datetime.now()

SkillFactory.primary_skill_list.append(Interference)

class Deceleration(PrimarySkill):
    name = "降速1级 - Deceleration Ⅰ"
    command = "降速"
    desc = \
        "使一个目标的速度降低2.00点\n"\
        "用法：降速 <目标>\n"\
        "例子：降速 5 | 使5号马的速度降低2.00点\n"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        msg = \
            f"技能生效：{self.name}\n"\
            f"目标 {target}号马 速度降低2.00"
        await bot.send(event, msg)
        horse_list[target - 1].speed -= 2.00
        self.last_used_time = datetime.datetime.now()

SkillFactory.primary_skill_list.append(Deceleration)

class GratisAnting(PrimarySkill):
    name = "白嫖1级 - Gratis Anting Ⅰ"
    command = "白嫖"
    desc = \
        "返还2点投注积分\n"\
        "用法：白嫖"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        if event.get_user_id() not in antes:
            await bot.send(event, f"{self.name}：该技能对未投注的使用者无效。", at_sender = True)
            return
        msg = \
            f"技能生效：{self.name}\n"\
            f"2点投注积分返还给使用者"
        await bot.send(event, msg)
        user = User.get_or_create_user(event.get_user_id())
        user.add_and_update(2)
        self.last_used_time = datetime.datetime.now()

SkillFactory.primary_skill_list.append(GratisAnting)

class PropertyReset(PrimarySkill):
    name = "重置1级 - Property Reset Ⅰ"
    command = "重置"
    desc = \
        "重置一个目标的属性\n"\
        "用法：重置 <目标>\n"\
        "例子：重置 2 | 重置2号马的属性"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        horse = horse_list[target - 1]
        new_horse = Horse(0)
        horse.speed, horse.death_rate, horse.stability = new_horse.speed, new_horse.death_rate, new_horse.stability
        msg = \
            f"技能生效：{self.name}\n" \
            f"重置了 {target}号马 的属性\n"\
            f"新规属性：速度{horse.speed:.2f}，不稳定性{horse.stability:.4f}，每步移动时意外出局率{horse.death_rate:.2%}"
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.primary_skill_list.append(PropertyReset)

class FalseStart(PrimarySkill):
    name = "抢跑1级 - False Start Ⅰ"
    command = "抢跑"
    desc = \
        "以三个单位缩短一个目标的跑道\n"\
        "用法：抢跑 <目标>\n"\
        "例子：抢跑 3 | 使3号马的跑道缩短三个单位"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        horse_list[target - 1].position += 3
        msg = \
            f"技能生效：{self.name}\n"\
            f"{target}号马的赛道被缩短三个单位\n"\
            f"{get_tracks_str(horse_list)}"
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.primary_skill_list.append(FalseStart)

class Anesthesia(PrimarySkill):
    name = "麻痹1级 - Anesthesia Ⅰ"
    command = "麻痹"
    desc = \
        "使一个目标的速度每秒降低0.80\n"\
        "用法：麻痹 <目标>\n"\
        "例子：麻痹 1 | 使1号马的速度每秒降低0.80"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        origin_move = horse_list[target - 1].move
        def newmove(self: Horse):
            self.speed -= 0.80
            origin_move()
        horse_list[target - 1].move = MethodType(newmove, horse_list[target - 1])
        msg = \
            f"技能生效：{self.name}\n"\
            f"{target}号马的速度将被以0.8/s的速度持续降低"
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.primary_skill_list.append(Anesthesia)


class Mirroring(PrimarySkill):
    name = "镜像1级 - Mirroring Ⅰ"
    command = "镜像"
    desc = \
        "使目标在3秒前某一瞬间反向移动\n"\
        "用法：镜像 <目标>\n"\
        "例子：镜像 2 | 使2号马在3秒前某一瞬间反向移动"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        origin_move = horse_list[target - 1].move
        move_count = 0
        reverse_round = random.randint(1, 3)
        def newmove(self: Horse):
            nonlocal move_count
            move_count += 1
            if move_count == reverse_round:
                self.position -= round(np.random.normal(self.speed, self.stability))
                if self.position < 0:
                    self.track_length -= self.position
                    self.position = 0
            else:
                origin_move()
        horse_list[target-1].move = MethodType(newmove, horse_list[target - 1])
        msg = \
            f"技能生效：{self.name}\n"\
            f"{target}号马将在3秒前反向移动"
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.primary_skill_list.append(Mirroring)

class Curse(PrimarySkill):
    name = "诅咒1级 - Curse Ⅰ"
    command = "诅咒"
    desc = \
        "提高目标每步意外出局率5%\n"\
        "用法：诅咒 <目标>\n"\
        "例子：诅咒 3: | 提高3号马途中出局率4%"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        horse_list[target - 1].death_rate += 0.04
        msg = \
            f"技能生效：{self.name}\n"\
            f"{target}号马的每步途中出局率提高4%"
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.primary_skill_list.append(Curse)

class ImmobilizationFetter(PrimarySkill):
    name = "定身1级 - Immobilization Fetter Ⅰ"
    command = "定身"
    desc = \
        "在开局定身目标3秒\n"\
        "用法：定身 <目标>\n"\
        "例子： 定身 4 | 定身4号马3秒"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        origin_move = horse_list[target - 1].move
        move_count = 0
        def newmove(self: Horse):
            nonlocal move_count
            if (move_count := move_count + 1) <= 3:
                return
            else:
                origin_move()
        horse_list[target-1].move = MethodType(newmove, horse_list[target - 1])
        msg = \
            f"技能生效：{self.name}\n"\
            f"{target}号马被定身3秒"
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.primary_skill_list.append(ImmobilizationFetter)

class Prophesy(PrimarySkill):
    name = "预言1级 - Prophesy Ⅰ"
    command = "预言"
    desc = \
        "预言目标的中途出局，成功将得到10点积分\n"\
        "用法：预言 <目标>\n"\
        "例子：预言 6 | 预言6号马的中途出局"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        origin_move = horse_list[target-1].move
        target_dead = False
        def newmove(self: Horse):
            nonlocal target_dead
            origin_move()
            if not target_dead and self.state == 'dead':
                target_dead = True
                User.get_or_create_user(event.get_user_id()).add_and_update(10)
        horse_list[target-1].move = MethodType(newmove, horse_list[target - 1])
        msg = \
            f"技能生效：{self.name}\n"\
            f"使用者会因为{target}号马的途中出局而获得10积分"
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.primary_skill_list.append(Prophesy)

class Purification(IntermediateSkill):
    name = "净化1级 - Purification Ⅰ"
    command = "净化"
    desc = \
        "免除所有中阶及以下技能的效果，每免除一个获得1点积分\n"\
        "用法：净化"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        for i in range(len(horse_list)):
            horse_list[i] = kwargs['origin_horse_list'][i]
        re_sk: Dict[str, List[Skill]] = kwargs['skill_list']
        skill_num = len(re_sk['primary'] + re_sk['intermediate'])
        re_sk['primary'] = []
        re_sk['intermediate'] = []
        User.get_or_create_user(event.get_user_id()).add_and_update(skill_num - 1)
        msg = \
            f"技能生效：{self.name}\n"\
            f"免除了所有已经使用技能的效果，并因此获得{skill_num-1}积分"
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.intermediate_skill_list.append(Purification)

class InvincibleState(IntermediateSkill):
    name = "金身1级 - Invincible State Ⅰ"
    command = "金身"
    desc = \
        "免除目标中途出局的可能性。已经被「火球」击杀的目标也可以复活\n"\
        "用法：金身 <目标>"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        origin_move = horse_list[target - 1].move
        def newmove(self: Horse):
            if self.state == 'dead':
                self.state = 'running'
            origin_move()
            if self.state == 'dead':
                self.state = 'running'
        horse_list[target-1].move = MethodType(newmove, horse_list[target - 1])
        msg = \
            f"技能生效：{self.name}\n"\
            f"免除{target}号马中途出局的可能性"
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.intermediate_skill_list.append(InvincibleState)

class Transsituation(IntermediateSkill):
    name = "移灯1级 - Transsituation Ⅰ"
    command = "移灯"
    desc = \
        "使目标在前三秒与另一目标位置互换\n"\
        "用法：移灯 <目标1> <目标2>"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target1, target2 = map(int, param.split())
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        origin_move = horse_list[target1 - 1].move
        move_count = 0
        trans_round = random.randint(1, 3)
        def newmove(self: Horse):
            nonlocal move_count, trans_round
            origin_move()
            move_count += 1
            if move_count == trans_round:
                self.position, horse_list[target2 - 1].position = horse_list[target2 - 1].position, self.position
        horse_list[target1 - 1].move = MethodType(newmove, horse_list[target1 - 1])
        msg = \
            f"技能生效：{self.name}\n"\
            f"{target1}号马和{target2}号马在三秒前会发生易位"
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.intermediate_skill_list.append(Transsituation)

class Catapult(IntermediateSkill):
    name = "弹射1级 - Catapult Ⅰ"
    command = "弹射"
    desc = \
        "使目标起步基础速度+5，但之后会恢复正常速度且每秒速度降低1点\n"\
        "用法：弹射 <目标>"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        origin_move = horse_list[target - 1].move
        def newmove(self: Horse):
            if self.state == 'stop':
                self.speed += 5
                origin_move()
                self.speed -= 5
            else:
                origin_move()
                self.speed -= (1 if self.speed > 1 else self.speed)
        horse_list[target - 1].move = MethodType(newmove, horse_list[target - 1])
        msg = \
            f"技能生效：{self.name}\n"\
            f"{target}号马的初始基础速度提升5，后续恢复并且每秒速度降1"
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.intermediate_skill_list.append(Catapult)

class GradualAdvance(IntermediateSkill):
    name = "慢热1级 - Gradual Advance Ⅰ"
    command = "慢热"
    desc = \
        "使目标的速度每秒提升1点\n"\
        "用法：慢热 <目标>"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        origin_move = horse_list[target - 1].move
        def newmove(self: Horse):
            origin_move()
            self.speed += 1
        horse_list[target - 1].move = MethodType(newmove, horse_list[target - 1])
        msg = \
            f"技能生效：{self.name}\n"\
            f"{target}号马每秒提速1点"
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.intermediate_skill_list.append(GradualAdvance)

class Homogenization(IntermediateSkill):
    name = "同一1级 - Homogenization Ⅰ"
    command = "同一"
    desc = \
        "以其中随机一匹马的属性同一化所有马的属性\n"\
        "用法：同一"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        target = random.randint(1, 6)
        for h in horse_list:
            h.stability = horse_list[target-1].stability
            h.death_rate = horse_list[target - 1].death_rate
            h.speed = horse_list[target - 1].speed
        msg = \
            f"技能生效：{self.name}\n"\
            f"所有马的属性被同化为{target}号马属性"
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.intermediate_skill_list.append(Homogenization)


class Counterbalance(IntermediateSkill):
    name = "制衡1级 - Conterbalance Ⅰ"
    command = "制衡"
    desc = \
        "多投注一个目标，如果指定的目标与下注目标相同，该技能无效\n"\
        "用法：制衡 <目标>"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        origin_move = horse_list[target - 1].move
        def newmove(self: Horse):
            origin_move()
            if self.finish_distance != 0:
                antes[event.get_user_id()] = target
        horse_list[target - 1].move = MethodType(newmove, horse_list[target - 1])
        msg = \
            f"技能生效：{self.name}\n"\
            f"多投注了{target}号马"
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.intermediate_skill_list.append(Counterbalance)

class Fireball(IntermediateSkill):
    name = "火球1级 - Fireball"
    command = "火球"
    desc = \
        "直接击杀目标\n"\
        "用法：火球 <目标>"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        horse_list[target - 1].state = 'dead'
        msg = \
            f"技能生效：{self.name}\n"\
            f"强制击杀了{target}号马"
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.intermediate_skill_list.append(Fireball)

class Mutation(IntermediateSkill):
    name = "异变1级 - Mutation Ⅰ"
    command = "异变"
    desc = \
        "重置所有目标属性\n"\
        "用法：异变"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        for h in horse_list:
            new_h = Horse(0)
            h.death_rate = new_h.death_rate
            h.stability = new_h.stability
            h.speed = new_h.speed
        msg = \
            f"技能生效：{self.name}\n"\
            f"重置了所有马的属性\n"\
            f"以下是新规属性\n"
        msg += '\n'.join(map(str, horse_list))
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.intermediate_skill_list.append(Mutation)

class Retribution(AdvancedSkill):
    name = "「惩戒」 - Retribution \N{Cross of Lorraine}"
    command = "惩戒"
    desc = \
        "「统治」：高阶技能会免除所有非高阶技能效果，但不会使其进入cd\n"\
        "「互斥」：高阶技能使用的情况下，不能再使用其他高阶技能\n"\
        "强制击杀目标，并获得对其下注所有积分的2倍\n"\
        "用法：惩戒 <目标>"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        horse_list[target - 1].death_icon = '\N{Cross of Lorraine}'
        horse_list[target - 1].state = 'dead'
        score = list(antes.values()).count(target)*4
        User.get_or_create_user(event.get_user_id()).add_and_update(score)
        msg = \
            f"{self.name}\n"\
            f"高阶技能发动\n"\
            f"强制击杀了{target}号马并取得{score}积分。"
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.advanced_skill_list.append(Retribution)

class Lightning(AdvancedSkill):
    name = "「雷击」 - Lightning \N{Electric Arrow}"
    command = "雷击"
    desc = \
        "「统治」：高阶技能会免除所有非高阶技能效果，但不会使其进入cd\n"\
        "「互斥」：高阶技能使用的情况下，不能再使用其他高阶技能\n"\
        "强制击杀三个目标\n"\
        "用法：雷击 <目标1> <目标2> <目标3>"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target1, target2, target3 = map(int, param.split())
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        horse_list[target1 - 1].state = horse_list[target2 - 1].state = horse_list[target3 - 1].state = 'dead'
        msg = \
            f"{self.name}\n"\
            f"高阶技能发动\n"\
            f"强制击杀了{target1}、{target2}、{target3}号马。"
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.advanced_skill_list.append(Lightning)

class TimeStop(AdvancedSkill):
    name = "「时停」 - Time Stop \N{White Hourglass}"
    command = "时停"
    desc = \
        "「统治」：高阶技能会免除所有非高阶技能效果，但不会使其进入cd\n"\
        "「互斥」：高阶技能使用的情况下，不能再使用其他高阶技能\n"\
        "指定一个目标为免除对象，其余四个目标在开局被定身4秒\n"\
        "用法：时停 <目标>"
    def __init__(self):
        super().__init__()
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        msg = \
            f"{self.name}\n"\
            f"高阶技能发动\n"\
            f"时停4秒，{target}为免除对象。"
        await bot.send(event, msg)
        for i in range(4):
            horse_list[target - 1].move()
            await bot.send(event, get_tracks_str(horse_list))
        self.last_used_time = datetime.datetime.now()

SkillFactory.advanced_skill_list.append(TimeStop)

class SpatiotemporalCrack(AdvancedSkill):
    name = "「裂缝」 - Spatiotemporal Crack \N{Rightwards Arrow Over Leftwards Arrow}"
    command = "裂缝"
    desc = \
        "「统治」：高阶技能会免除所有非高阶技能效果，但不会使其进入cd\n"\
        "「互斥」：高阶技能使用的情况下，不能再使用其他高阶技能\n"\
        "缩短一个目标跑道的一半\n"\
        "用法：裂缝 <目标>"    
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        msg = \
            f"{self.name}\n"\
            f"高阶技能发动\n"\
            f"{target}的跑道被缩短一半。"
        horse_list[target - 1].track_length = round(horse_list[target - 1].track_length / 2)
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.advanced_skill_list.append(SpatiotemporalCrack)

class Manoeuvre(AdvancedSkill):
    name = "「操纵」 - Manoeuvre \N{Left Right Wave Arrow}"
    command = "操纵"
    desc = \
        "「统治」：高阶技能会免除所有非高阶技能效果，但不会使其进入cd\n"\
        "「互斥」：高阶技能使用的情况下，不能再使用其他高阶技能\n"\
        "互换两个目标的属性\n"\
        "用法：操纵 <目标1> <目标2>"
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target1, target2 = map(int, param.split())
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        msg = \
            f"{self.name}\n"\
            f"高阶技能发动\n"\
            f"互换了{target1}号马和{target2}号马的属性。"
        horse_list[target1 - 1].speed, horse_list[target2 - 1].speed = horse_list[target2 - 1].speed, horse_list[target1 - 1].speed
        horse_list[target1 - 1].stability, horse_list[target2 - 1].stability = horse_list[target2 - 1].stability, horse_list[target1 - 1].stability
        horse_list[target1 - 1].death_rate, horse_list[target2 - 1].death_rate = horse_list[target2 - 1].death_rate, horse_list[target1 - 1].death_rate
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.advanced_skill_list.append(Manoeuvre)

class Blessing(AdvancedSkill):
    name = "「祝福」 - Blessing \N{Floral Heart}"
    command = "祝福"
    desc = \
        "「统治」：高阶技能会免除所有非高阶技能效果，但不会使其进入cd\n"\
        "「互斥」：高阶技能使用的情况下，不能再使用其他高阶技能\n"\
        "将目标中途出局率以1%对应1点速度进行转换\n"\
        "用法：祝福 <目标1>"
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。", at_sender = True)
            return
        msg = \
            f"{self.name}\n"\
            f"高阶技能发动\n"\
            f"将{target}号马的中途出局率转换为速度。"
        horse_list[target - 1].speed += horse_list[target - 1].death_rate*100
        horse_list[target - 1].death_rate = 0.0
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.advanced_skill_list.append(Blessing)

class Teleport(AdvancedSkill):
    name = "「传送」 - Teleport \N{White Flag}"
    command = "传送"
    desc = \
        "「统治」：高阶技能会免除所有非高阶技能效果，但不会使其进入cd\n"\
        "「互斥」：高阶技能使用的情况下，不能再使用其他高阶技能\n"\
        "将目标传送至中途随机位置起跑\n"\
        "用法：传送 <目标1>"
    async def use(self, bot: Bot, event: GroupMessageEvent, horse_list: List[Horse], antes: Dict[str, int], param: str, **kwargs):
        try:
            target = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的技能使用口令。")
            return
        msg = \
            f"{self.name}\n"\
            f"高阶技能发动\n"\
            f"将{target}号马传送至中途位置起跑"
        horse_list[target - 1].position = random.randint(0, horse_list[target - 1].track_length - 1)
        await bot.send(event, msg)
        self.last_used_time = datetime.datetime.now()

SkillFactory.advanced_skill_list.append(Teleport)