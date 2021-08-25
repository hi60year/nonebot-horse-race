from typing import Dict
import mysql.connector
import json
from .goods import shop_list, Goods, shop_name_dict_getter
from typing import Type
from nonebot.adapters import Bot
from nonebot.adapters.cqhttp import GroupMessageEvent

mysql_connect_config = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'calenderbot',
}

create_user = "INSERT INTO backpack_table (qq_num, backpack) VALUES (%s, %s)"
query_user = "SELECT qq_num, backpack FROM backpack_table WHERE qq_num = %s"
update_user = "UPDATE backpack_table SET backpack = %s WHERE qq_num = %s"

shop_name_dict = shop_name_dict_getter()

class User:
    def __init__(self, qq_num: str , backpack: Dict[Type[Goods], int] = {}):
        self.qq_num : str = qq_num
        self.backpack : Dict[Type[Goods], int] = backpack

    @classmethod
    def get_user(cls, qq_num: str):
        cnx = mysql.connector.connect(**mysql_connect_config)
        cursor = cnx.cursor()
        cursor.execute(query_user, (qq_num,))
        res = cursor.fetchone()
        cursor.close()
        cnx.close()
        if not res:
            return None
        else:
            return cls(qq_num, cls.backpack_deserializer(res[1]))

    @classmethod
    def create_user(cls, qq_num: str):
        cnx = mysql.connector.connect(**mysql_connect_config)
        cursor = cnx.cursor()
        cursor.execute(create_user, (qq_num, cls(qq_num).backpack_serializer()))
        cnx.commit()
        cursor.close()
        cnx.close()
    
    @classmethod
    def get_or_create_user(cls, qq_num: str):
        if (res := cls.get_user(qq_num)) is None:
            cls.create_user(qq_num)
            return cls.get_user(qq_num)
        else:
            return res

    async def use_item(self, item: Type[Goods], bot: Bot, event: GroupMessageEvent, param: str):
        if item not in self.backpack:
            return False
        elif self.backpack[item] == 1:
            self.backpack.pop(item)
        else:
            self.backpack[item] -= 1
        if not await item().use(bot, event, param):
            self.add_item(item)
        cnx = mysql.connector.connect(**mysql_connect_config)
        cursor = cnx.cursor()
        cursor.execute(update_user, (self.backpack_serializer(), self.qq_num))
        cnx.commit()
        cursor.close()
        cnx.close()
        return True

    def add_item(self, item: Type[Goods]):
        if item not in self.backpack:
            self.backpack[item] = 1
        else:
            self.backpack[item] += 1
        cnx = mysql.connector.connect(**mysql_connect_config)
        cursor = cnx.cursor()
        cursor.execute(update_user, (self.backpack_serializer(), self.qq_num))
        cnx.commit()
        cursor.close()
        cnx.close()

    def get_desc(self):
        msg = f"这是用户{self.qq_num}的背包信息：\n"
        msg += '\n'.join(map(lambda x: f"{x[0].name}：{x[1]}件", self.backpack.items()))
        return msg

    def backpack_to_dict(self):
        return dict(map(lambda x: (x[0].name, x[1]) ,self.backpack.items()))

    def backpack_serializer(self):
        return json.dumps(self.backpack_to_dict())
    
    @classmethod
    def backpack_deserializer(cls, data: str):
        obj = json.loads(data)
        obj = dict(map(lambda x: (shop_name_dict[x[0]], x[1]), obj.items()))
        return obj