# import nonebot
from nonebot import get_driver, on_message
from nonebot.adapters import Event, Bot
from nonebot.typing import T_State
import time
import mysql.connector
from nonebot.plugin import require
from .config import Config

global_config = get_driver().config
config = Config(**global_config.dict())

Score = require('score_system')

mysql_connect_config = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'calenderbot',
}

query_assign = 'SELECT * FROM assign_table WHERE assign_time > str_to_date(%s, "%Y-%m-%d") AND qq_num = %s'
insert_assign = 'INSERT INTO assign_table (qq_num) VALUES (%s)'


assignEvent = on_message(priority=5)

@assignEvent.handle()
async def assign(bot: Bot, event: Event, state: T_State) -> None:
    if str(event.get_message()).strip() == '签到':
        try: cnx = mysql.connector.connect(**mysql_connect_config)
        except mysql.connector.Error:
            await assignEvent.finish("抱歉，数据库连接出现错误，签到失败。", at_sender = True)
        cursor = cnx.cursor()
        cursor.execute(query_assign, (time.strftime("%Y-%m-%d"), event.get_user_id()))
        if cursor.fetchone():
            await assignEvent.finish("您今天已经签到过了哦！", at_sender= True)
        else:
            cursor.execute(insert_assign, (event.get_user_id(),))
            cnx.commit()
            user = Score.User.get_or_create_user(event.get_user_id())
            user.add_and_update(5)
            await assignEvent.finish("签到成功，积分+5", at_sender = True)
        cursor.close()
        cnx.close()
