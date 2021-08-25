# import nonebot
from io import TextIOWrapper
from nonebot import get_driver, on_message
import nonebot
import json
import os
import mysql.connector
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event

from .config import Config

global_config = get_driver().config
config = Config(**global_config.dict())

mysql_connect_config = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'calenderbot',
}

query_user = "SELECT qq_num, score FROM score_table WHERE qq_num = %s"
create_user = "INSERT INTO score_table (qq_num) VALUES (%s)"
update_user = "UPDATE score_table SET score = %s WHERE qq_num = %s"

# Export something for other plugin
export = nonebot.export()

@export
class User:

    def __init__(self, qq_num, score):
        self.qq_num = qq_num
        self.score = score
    
    def update(self):
        cnx = mysql.connector.connect(**mysql_connect_config)
        cursor = cnx.cursor()
        cursor.execute(update_user, (self.score, self.qq_num))
        cnx.commit()
        cursor.close()
        cnx.close()
    
    def add_and_update(self, score_change):
        self.score += score_change
        self.update()
    
    def get_score(self):
        return self.score

    @staticmethod
    def get_user(qq_num: str):
        cnx = mysql.connector.connect(**mysql_connect_config)
        cursor = cnx.cursor()
        cursor.execute(query_user, (qq_num,))
        res = cursor.fetchone()
        cursor.close()
        cnx.close()
        if res:
            return User(*res)
        else:
            return None
    
    @staticmethod
    def create_user(qq_num: str):
        cnx = mysql.connector.connect(**mysql_connect_config)
        cursor = cnx.cursor()
        cursor.execute(create_user, (qq_num,))
        cnx.commit()
        cursor.close()
        cnx.close()
    
    @staticmethod
    def get_or_create_user(qq_num: str):
        if not (user := User.get_user(qq_num)):
            User.create_user(qq_num)
            return User.get_user(qq_num)
        else:
            return user

question_score = on_message(priority=5)

export.question_score_sheet = ['积分', '积分查询', '查询积分', '当前积分', 'score', 'score query']

@question_score.handle()
async def handler(bot: Bot, event: Event, state: T_State):
    msg = str(event.get_message()).strip()
    if msg in export.question_score_sheet:
        try:
            user = User.get_or_create_user(event.get_user_id())
        except Exception as e:
            await question_score.finish(f"抱歉，出现问题，目前无法查询积分{e}", at_sender = True)
        await question_score.finish(f"您目前的积分是{user.get_score()}", at_sender = True)

question_ranking = on_message(priority=5)
export.question_ranking_sheet = ['排行榜', 'top', 'ranking']
get_ranking = "SELECT qq_num, score FROM score_table ORDER BY score DESC LIMIT 5"

@question_ranking.handle()
async def question_ranking_handler(bot: Bot, event: Event):
    if not str(event.get_message()) in export.question_ranking_sheet:
        return
    res = []
    msg = "当前积分排行榜：\n"
    try:
        cnx = mysql.connector.connect(**mysql_connect_config)
        cursor = cnx.cursor()
        cursor.execute(get_ranking, tuple())
        res = cursor.fetchall()
    except Exception as e:
        await question_ranking.finish(f"抱歉，发生错误\n{e}", at_sender = True)
    finally:
        cursor.close()
        cnx.close()
    if not res:
        await question_ranking.finish("目前排行榜空空如也哦，快来抢占位置！")
    else:
        for i, (qq_num, score) in enumerate(res, start=1):
            msg += f"第{i}名 {qq_num} {score}分\n"
        await question_ranking.finish(msg)
