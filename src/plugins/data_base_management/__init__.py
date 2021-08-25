# import nonebot
from nonebot import get_driver, on_command
from nonebot.permission import SUPERUSER
from nonebot.adapters import Bot, Event
from nonebot.typing import T_State
import mysql.connector

from .config import Config

global_config = get_driver().config
config = Config(**global_config.dict())

mysql_connect_config = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'calenderbot',
}

database_control = on_command("db-control", permission=SUPERUSER, priority=1)
denied_database_control = on_command("db-control", priority=5)

@denied_database_control.handle()
async def denied_db_control(bot: Bot, event: Event, state: T_State):
    if not event.get_user_id() in global_config.dict()['superusers']:
        await denied_database_control.finish("--ERROR: ACCESS DENIED--")

command = ""

@database_control.handle()
async def db_control(bot: Bot, event: Event, state: T_State):
    global command
    command = ""
    await bot.send(event, "--Warning: data base control started. Running with superuser privilege--")

@database_control.got("finish", prompt=">")
async def db_control_input(bot: Bot, event: Event, state: T_State):
    global command
    s = str(event.get_message())
    if s.strip() == "execute select":
        cnx = mysql.connector.connect(**mysql_connect_config)
        cursor = cnx.cursor()
        await bot.send(event, "executing...", at_sender=True)
        try:
            cursor.execute(command, tuple())
            await bot.send(event, '\n' + str(cursor.fetchall()), at_sender=True)
        except Exception as e:
            await bot.send(event, f"error(s) detected. \n{e}")
        finally:
            state['finish'] = True
            cursor.close()
            cnx.close()
            await database_control.finish("--Database control exited--")
    elif s.strip() == "execute commit":
        cnx = mysql.connector.connect(**mysql_connect_config)
        cursor = cnx.cursor()
        await bot.send(event, "executing...", at_sender=True)
        try:
            cursor.execute(command, tuple())
            cnx.commit()
        except Exception as e:
            await bot.send(event, f"error(s) detected. \n{e}")
        finally:
            state['finish'] = True
            cursor.close()
            cnx.close()
            await database_control.finish("--Database control exited--")
    else:
        command += s
        await database_control.reject('>')