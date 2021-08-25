from abc import ABC, abstractmethod
from typing import Type, List
from skill import SkillFactory, PrimarySkill, IntermediateSkill, AdvancedSkill
from nonebot.adapters import Bot
from nonebot.adapters.cqhttp import GroupMessageEvent
import mysql.connector
import skill_system as sksys
import random

mysql_connect_config = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'calenderbot',
}
class Goods(ABC):
    price: int
    desc: str
    name: str

    @abstractmethod
    async def use(self, bot: Bot, event: GroupMessageEvent, param: str) -> bool:
        pass

shop_list : List[Type[Goods]] = []

def shop_name_dict_getter():
    return {goods.name : goods for goods in shop_list}

class SkillBook(Goods):
    pass

class PrimarySkillBook(SkillBook):
    price: int = 10
    name = "初阶技能书"
    desc = \
f"""
{name}
价格{price}积分
使用这个道具可以随机获得一个初阶技能。初阶技能总共可以装配三个，满载后可以通过再次使用此道具重置技能。
使用方法：{name} <技能槽>
其中技能槽是1~3的整数
""".strip()

    async def use(self, bot: Bot, event: GroupMessageEvent, param: str) -> bool:
        user = sksys.User.get_or_create_user(event.get_user_id())
        try:
            slot = int(param)
        except ValueError:
            await bot.send(event, f"{self.name}：错误的使用口令。", at_sender = True)
            return False
        if slot > 3 or slot < 1:
            await bot.send(event, f"{self.name}：错误的使用口令。", at_sender = True)
            return False
        await bot.send(event, "Cal子祈祷中...")
        skill_type: Type[PrimarySkill] = random.choice([i for i in SkillFactory.primary_skill_list if i not in map(type, user.primary_skills)])
        user.primary_skills[slot-1] = skill_type()
        await bot.send(event, f"新规技能获得成功。位于初阶技能槽{slot}的技能变更为\n{user.primary_skills[slot-1].get_desc()}")
        user.update_skill('primary_skill_list', user.primary_skills)
        return True

shop_list.append(PrimarySkillBook)

class IntermediateSkillBook(SkillBook):
    price: int = 25
    name = "中阶技能书"
    desc = \
        f"{name}\n"\
        f"价格{price}积分\n"\
        f"使用这个道具可以随机获得一个中阶技能，中阶技能每人只能持有一个，满载后可通过此道具重置技能。\n"\
        f"使用方法：{name}"

    async def use(self, bot: Bot, event: GroupMessageEvent, param: str) -> bool:
        user = sksys.User.get_or_create_user(event.get_user_id())
        await bot.send(event, "Cal子祈祷中...")
        skill_type: Type[IntermediateSkill] = random.choice(SkillFactory.intermediate_skill_list)
        user.intermediate_skill = skill_type()
        await bot.send(event, f"新规技能获得成功。位于中阶技能槽的技能变更为{user.intermediate_skill.get_desc()}")
        user.update_skill('intermediate_skill', user.intermediate_skill)
        return True

shop_list.append(IntermediateSkillBook)

class AdvancedSkillBook(SkillBook):
    price: int = 75
    name = "高阶技能书"
    desc = \
        f"{name}\n"\
        f"价格{price}积分\n"\
        f"使用这个道具可以随机获得一个高阶技能，高阶技能每人只能持有一个，满载后可通过此道具重置技能。\n"\
        f"使用方法：{name}"

    async def use(self, bot: Bot, event: GroupMessageEvent, param: str) -> bool:
        user = sksys.User.get_or_create_user(event.get_user_id())
        await bot.send(event, "Cal子祈祷中...")
        skill_type: Type[AdvancedSkill] = random.choice(SkillFactory.advanced_skill_list)
        user.advanced_skill = skill_type()
        await bot.send(event, f"新规技能获得成功。位于高阶技能槽的技能变更为{user.advanced_skill.get_desc()}")
        user.update_skill('advanced_skill', user.advanced_skill)
        return True

shop_list.append(AdvancedSkillBook)