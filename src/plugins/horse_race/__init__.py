# import nonebot
import random
from nonebot import get_driver, on_message, on_startswith
from nonebot.plugin import require
import horse
from nonebot.adapters import Bot
from nonebot.adapters.cqhttp import GroupMessageEvent
from nonebot.typing import T_State
from .config import Config
from ..skill import Skill, SkillFactory
import re
from pampy import match, _
from horse import Horse, get_tracks_str
import asyncio
from typing import Dict, List
import skill_system as sksys
import datetime
from copy import deepcopy

global_config = get_driver().config
config = Config(**global_config.dict())

Score = require('score_system')

group_antes: Dict[int, Dict[str, int]] = {}
horse_lists: Dict[int, List[Horse]] = {}
origin_horse_lists: Dict[int, List[Horse]] = {}
skill_enabled_set = set()
readied_skills = {}

game_ready = on_message(priority = 5)

@game_ready.handle()
async def game_ready_handler(bot: Bot, event: GroupMessageEvent):
    if(str(event.get_message()).strip() == '赛马'):
        if event.group_id == 227511507:
            await game_ready.send("这个群规定了不能赛马哦~赛马请加msc迎新群", at_sender = True)
            return None
        if event.group_id in group_antes:
            await game_ready.finish("当前群组已经有一场赛马比赛正在进行，请等待比赛结束后再开始", at_sender = True)
            return None
        group_antes[event.group_id] = {}
        horse_list = [horse.Horse(i) for i in range(1, 7)]
        horse_lists[event.group_id] = horse_list
        tracks = get_tracks_str(horse_list)
        await bot.send(event, "赛马即将开始\n" + tracks)
        await bot.send(event, "以下是马的属性信息\n{}".format('\n'.join(map(str, horse_list))))
        await bot.send(event, "请输入 下注 x号马 进行下注，每次下注需要2积分。注意：所下注的马的属性越差，胜利后所得收益就越高；投注人数达到5人时开始赛马")
    
anting = on_message(priority = 5, block = True)

@anting.handle()
async def anting_handler(bot: Bot, event: GroupMessageEvent):
    pattern = r'^下注\s*(\d)\s*号马$'
    mat_res = re.match(pattern, str(event.get_message()).strip())
    if mat_res is not None:
        if event.group_id not in group_antes:
            await anting.finish("都没在赛马你下什么注嘛！TwT", at_sender = True)
            return

        try:
            user = Score.User.get_or_create_user(event.get_user_id())
        except:
            await anting.finish("发生数据库异常")
            return

        if user.get_score() < 2:
            await anting.finish("你的积分不够啦，还不快去签到！awa", at_sender = True)
            return
        
        if event.get_user_id() in group_antes[event.group_id]:
            await anting.finish("你已经下过注啦，不可以重复下注哦", at_sender = True)
            return
        
        if len(group_antes[event.group_id]) >= 5:
            await anting.finish("比赛进行当中，不可以再下注了哦", at_sender = True)
            return

        try:
            user.add_and_update(-2)
        except:
            await anting.finish("发生数据库异常")
            return
        
        group_antes[event.group_id][event.get_user_id()] = int(mat_res[1])
        await bot.send(event, f"您已经成功投注{mat_res[1]}号马", at_sender = True)

        if len(group_antes[event.group_id]) >= 5:
            await skill_waiter(bot, event)

async def skill_waiter(bot: Bot, event: GroupMessageEvent):
    origin_horse_lists[event.group_id] = deepcopy(horse_lists[event.group_id])
    ohl = origin_horse_lists[event.group_id]
    await bot.send(event, "--进入技能使用阶段30s--")
    readied_skills[event.group_id] = {}
    re_sk = readied_skills[event.group_id]
    re_sk['primary'] = []
    re_sk['intermediate'] = []
    re_sk['advanced'] = []
    skill_enabled_set.add(event.group_id)
    await asyncio.sleep(30)
    skill_enabled_set.remove(event.group_id)
    if re_sk['advanced']:
        await bot.send(event, "「统治」：由于高阶技能的存在，所有其他技能无效化。")
        re_sk["primary"] = []
        re_sk['intermediate'] = []
    for i, evt, param in re_sk['advanced']:
        i: Skill
        evt: GroupMessageEvent
        param: str
        if (delta := i.cd_remain()):
            await bot.send(event, f"{i.name}：技能处于cd当中, 距离下次使用还有{delta}")
        else:
            await i.use(bot, evt, horse_lists[event.group_id], group_antes[event.group_id], param,
                origin_horse_list = ohl, skill_list = re_sk)
            sksys.User.get_or_create_user(evt.get_user_id()).update_skill('advanced_skill', i)
    for i, evt, param in re_sk['intermediate']:
        i: Skill
        evt: GroupMessageEvent
        param: str
        if (delta := i.cd_remain()):
            await bot.send(event, f"{i.name}：技能处于cd当中, 距离下次使用还有{delta}")
        else:
            await i.use(bot, evt, horse_lists[event.group_id], group_antes[event.group_id], param,
                origin_horse_list = ohl, skill_list = re_sk)
            sksys.User.get_or_create_user(evt.get_user_id()).update_skill('intermediate_skill', i)
    for i, evt, param, slot in re_sk['primary']:
        i: Skill
        evt: GroupMessageEvent
        param: str
        if (delta := i.cd_remain()):
            await bot.send(event, f"{i.name}：技能处于cd当中, 距离下次使用还有{delta}")
        else:
            await i.use(bot, evt, horse_lists[event.group_id], group_antes[event.group_id], param,
                origin_horse_list = ohl, skill_list = re_sk)
            user = sksys.User.get_or_create_user(evt.get_user_id())
            user.primary_skills[slot] = i
            user.update_skill('primary_skill_list', user.primary_skills)
    await start_game(bot, event)

skill_use = on_startswith("技能", priority = 5)

@skill_use.handle()
async def skill_use_handler(bot: Bot, event: GroupMessageEvent):
    if event.group_id not in skill_enabled_set:
        return
    re_sk = readied_skills[event.group_id]
    msg_input = str(event.get_message()).strip()
    args = [i for i in msg_input.split() if i != '']
    if args[0] != "技能":
        return
    if args[1] not in SkillFactory.get_skill_name_dict():
        await skill_use.finish("未找到这个技能哦，请检查拼写", at_sender = True)
        return
    skill_type = SkillFactory.get_skill_name_dict()[args[1]]
    if skill_type not in map(type, (user := sksys.User.get_or_create_user(event.get_user_id())).primary_skills + [user.intermediate_skill] + [user.advanced_skill]):
        await skill_use.finish("不可以使用您暂时未拥有的技能哦", at_sender = True)
    if (skill_type, event.get_user_id()) in map(lambda x: (type(x[0]), x[1].get_user_id()), re_sk['primary'] + re_sk['intermediate'] + re_sk['advanced']):
        await skill_use.finish("禁止重复使用相同技能", at_sender = True)
    for slot, sk in enumerate(user.primary_skills):
        if isinstance(sk, skill_type):
            re_sk['primary'].append((sk, event, ' '.join(args[2:]), slot))
    if isinstance(user.intermediate_skill, skill_type):
        re_sk['intermediate'].append((user.intermediate_skill, event, ' '.join(args[2:])))
    elif isinstance(user.advanced_skill, skill_type):
        if re_sk['advanced']:
            await skill_use.finish("「互斥」：高阶技能使用的情况下，不能再使用其他高阶技能", at_sender = True)
        else:
            re_sk['advanced'].append((user.advanced_skill, event, ' '.join(args[2:])))
    await skill_use.finish("使用技能成功", at_sender = True)
        
async def start_game(bot: Bot, event: GroupMessageEvent):
    await bot.send(event, "--比赛正式开始--")
    horse_list: list[horse.Horse] = horse_lists[event.group_id]
    finished = False

    while True:
        await asyncio.sleep(1)
        for h in horse_list:
            origin_state = h.state
            h.move()
            if h.state == 'dead' and origin_state != 'dead':
                await bot.send(event, f"{h.number}号马因为{random.choice(horse.Horse.death_reason)}意外退场！")
            if h.finish_distance != 0:
                finished = True
        if finished:
            winner = max(horse_list, key = lambda h: h.finish_distance)
            for h in horse_list:
                if h.finish_distance != 0 and h != winner: h.position -= 1
            await bot.send(event, get_tracks_str(horse_list))
            await bot.send(event, f"胜者是{winner.number}号马！")
            await reward(bot, event, origin_horse_lists[event.group_id], winner.number)
            break
        elif all([h.state == 'dead' for h in horse_list]):
            await bot.send(event, get_tracks_str(horse_list))
            await bot.send(event, "所有马都死翘翘拉！没有胜者")
            break

        await bot.send(event, get_tracks_str(horse_list))
    group_antes.pop(event.group_id)
    horse_lists.pop(event.group_id)

async def reward(bot: Bot, event: GroupMessageEvent, horse_list: list[horse.Horse], winner: int):
    winner -= 1
    basic_score = 2
    speed_rank = sorted(horse_list, key= lambda x: x.speed, reverse=True).index(horse_list[winner]) + 1
    basic_score += match(speed_rank,
                         2, 1,
                         3, 2,
                         4, 4,
                         5, 10,
                         6, 15,
                         _, 0)
    death_rate = horse_list[winner].death_rate
    if death_rate > .05:
        basic_score += 2
    elif death_rate > .07:
        basic_score += 4
    elif death_rate > .09:
        basic_score += 6
    elif death_rate > .12:
        basic_score += 10
    elif death_rate > .15:
        basic_score += 15
    extra = random.randint(1,2)
    basic_score += extra
    await bot.send(event, f"根据马的综合评定，给予猜中者每人{basic_score*2}分的奖励！")
    for (user, guess) in group_antes[event.group_id].items():
        if guess == winner + 1:
            Score.User.get_or_create_user(user).add_and_update(basic_score*2)
    
    
