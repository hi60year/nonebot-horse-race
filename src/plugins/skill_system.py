from logging import error
from mysql.connector.errors import Error
import skill as sk
from typing import List, Tuple, Union
import mysql.connector
from skill import AdvancedSkill, IntermediateSkill, PrimarySkill, Skill, SkillFactory
import json

mysql_connect_config = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'calenderbot',
}

query_user = "SELECT qq_num, primary_skill_list, intermediate_skill, advanced_skill FROM skill_table WHERE qq_num = %s"
create_user = "INSERT INTO skill_table (qq_num, primary_skill_list, intermediate_skill, advanced_skill) VALUES (%s, %s, %s, %s)"
update_user = "UPDATE skill_table SET {} = %s WHERE qq_num = %s"

class User:
    def __init__(self, qq_num: str, primary_skills: List[sk.PrimarySkill] = [None, None, None],
                               intermediate_skill: Union[sk.IntermediateSkill, None] = None,
                               advanced_skill : Union[sk.AdvancedSkill, None] = None):
        self.qq_num = qq_num
        self.primary_skills : List[sk.PrimarySkill, None] = primary_skills
        self.intermediate_skill : Union[sk.IntermediateSkill, None] = intermediate_skill
        self.advanced_skill : Union[sk.AdvancedSkill, None] = advanced_skill
    @classmethod
    def create_user(cls, qq_num):
        cnx = mysql.connector.connect(**mysql_connect_config)
        cursor = cnx.cursor()
        user = cls(qq_num)
        cursor.execute(create_user, (qq_num, json.dumps([SkillFactory.skill_serializer(i) for i in user.primary_skills]),
                                             SkillFactory.skill_serializer(user.intermediate_skill),
                                             SkillFactory.skill_serializer(user.advanced_skill)))
        cnx.commit()
        cursor.close()
        cnx.close()
    
    @classmethod
    def get_user(cls, qq_num):
        cnx = mysql.connector.connect(**mysql_connect_config)
        cursor = cnx.cursor()
        cursor.execute(query_user, (qq_num,))
        res: Tuple = cursor.fetchone()
        cursor.close()
        cnx.close()
        if not res:
            return None
        else:
            return cls(res[0], [SkillFactory.skill_deserializer(i) for i in json.loads(res[1])], 
                               SkillFactory.skill_deserializer(res[2]),
                               SkillFactory.skill_deserializer(res[3]))

    @classmethod
    def get_or_create_user(cls, qq_num):
        if (user := cls.get_user(qq_num)) is None:
            cls.create_user(qq_num)
            return cls.get_user(qq_num)
        else:
            return user

    def update_skill(self, skill_type: str, skill: Union[IntermediateSkill, AdvancedSkill, List[PrimarySkill]]):
        cnx = mysql.connector.connect(**mysql_connect_config)
        cursor = cnx.cursor()
        if skill_type == 'primary_skill_list':
            cursor.execute(update_user.format(skill_type), (json.dumps([SkillFactory.skill_serializer(i) for i in skill]), self.qq_num))
        else:
            cursor.execute(update_user.format(skill_type), (SkillFactory.skill_serializer(skill), self.qq_num))
            
        cnx.commit()
        cursor.close()
        cnx.close()