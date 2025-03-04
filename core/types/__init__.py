# -*- coding: utf-8 -*-
"""
@Description:
@Date       : 2024/9/4 22:38
@Author     : lkkings
@FileName:  : __init__.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from abc import ABC
from dataclasses import dataclass, asdict


@dataclass
class DataType:
    def to_dict(self):
        return asdict(self)


@dataclass
class Serializable(DataType):

    def deserialize(self):
        pass


@dataclass
class Serial(DataType):

    def serialize(self):
        pass
