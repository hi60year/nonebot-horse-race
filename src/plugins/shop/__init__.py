# import nonebot
from typing import Union
from nonebot import get_driver, on_message, rule, on_startswith
import nonebot
import mysql.connector
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from .config import Config
from nonebot.adapters.cqhttp import GroupMessageEvent
from .goods import shop_list, shop_name_dict_getter
import score_system as sc
from . import backpack as bp
import re
import skill_system as sksys
from skill import Skill

global_config = get_driver().config
config = Config(**global_config.dict())

shop = on_startswith('商店', priority = 5)

@shop.handle()
async def shop_handler(bot: Bot, event: GroupMessageEvent):
    msg = "欢迎光临cal子的商店！>v<\n现在商店中在售的商品如下：\n"
    msg += '\n'.join(map(lambda x: f"{x[0]} | {x[1].name} | {x[1].price}积分", enumerate(shop_list)))
    msg += "\n输入 购买 <商品号> 来购买商品哦~"
    await shop.finish(msg)

buy = on_startswith('购买', priority = 5)

@buy.handle()
async def buy_handler(bot: Bot, event: GroupMessageEvent):
    msg_input = str(event.get_message()).strip()
    res = re.match(r'购买\s*(\d+)', msg_input)
    if res is None:
        return
    num = int(res[1])
    try:
        target = shop_list[num]
    except IndexError:
        await buy.finish("请不要尝试购买不存在的商品", at_sender = True)
        return
    user = sc.User.get_or_create_user(event.get_user_id())
    if user.score < target.price:
        await buy.finish("您的积分不够，快去攒够积分吧", at_sender = True)
        return
    user.add_and_update(-target.price)
    user = bp.User.get_or_create_user(event.get_user_id())
    user.add_item(target)
    await buy.finish(f"成功购买{target.name}，积分-{target.price}\n谢谢惠顾欢迎下次光临QwQ")

show_backpack = on_startswith('背包', priority = 5)

@show_backpack.handle()
async def show_backpack_handler(bot: Bot, event: GroupMessageEvent):
    await show_backpack.finish(bp.User.get_or_create_user(event.get_user_id()).get_desc())

goods_using = on_startswith('使用', priority = 5)
@goods_using.handle()
async def goods_using_handler(bot: Bot, event: GroupMessageEvent):
    msg_input = str(event.get_message()).strip()
    args = [i for i in msg_input.split() if i != '']
    if len(args) <= 1 or args[0] != '使用':
        return
    elif args[1] not in shop_name_dict_getter():
        await goods_using.finish("请不要试图使用不存在的物品哦", at_sender = True)
        return
    elif (type := shop_name_dict_getter()[args[1]]) not in (user := bp.User.get_or_create_user(event.get_user_id())).backpack:
        await goods_using.finish("您的该物品余量不足，请前往商店购买哦", at_sender = True)
    else:
        await user.use_item(type, bot, event, ' '.join(args[2:]))

def get_skill_str(skill: Union[Skill, None]) -> str:
    if skill is None:
        return "未实装"
    msg = f"{skill.name} "
    if (cd := skill.cd_remain()):
        msg += f'cd: {cd}'
    else:
        msg += '就绪'
    return msg

show_skills = on_startswith('技能', priority = 5)
@show_skills.handle()
async def show_skills_handler(bot: Bot, event:GroupMessageEvent):
    if str(event.get_message()).strip() != '技能':
        return
    user = sksys.User.get_or_create_user(event.get_user_id())
    msg = \
        f"用户{user.qq_num}的技能信息如下：\n"\
        f"初阶技能1：{get_skill_str(user.primary_skills[0])}\n"\
        f"初阶技能2：{get_skill_str(user.primary_skills[1])}\n"\
        f"初阶技能3：{get_skill_str(user.primary_skills[2])}\n"\
        f"中阶技能：{get_skill_str(user.intermediate_skill)}\n"\
        f"高阶技能：{get_skill_str(user.advanced_skill)}\n"
    await show_skills.finish(msg)