# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/4 21:01
@Author     : lkkings
@FileName:  : json_utils.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import json


class JSONUtil:
    @classmethod
    def parse2obj(cls, data, obj_class):
        parseData = json.loads(data.strip('\t\r\n'))
        result = obj_class()
        result.__dict__ = parseData
        return result
