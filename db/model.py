# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/15 14:57
@Author     : lkkings
@FileName:  : model.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
import json
import os
from typing import List, Dict

import aiohttp
from tortoise import fields, Model


class Token(Model):
    symbol = fields.CharField(max_length=24)
    name = fields.CharField(max_length=1024)
    mint = fields.CharField(max_length=44, unique=True, index=True)
    decimals = fields.SmallIntField()
    extensions = fields.CharField(max_length=1024)  #  代币的扩展信息，可能包含一些额外的元数据或与代币相关的扩展信息。
    icon = fields.CharField(max_length=128)
    hasFreeze = fields.BooleanField(default=False)

    __temp__: Dict[str, 'Token'] = {}

    @classmethod
    async def get_symbol(cls, mint: str):
        token = cls.__temp__.get(mint)
        if not token:
            token = await cls.get_or_none(mint=mint)
            cls.__temp__[mint] = token
        return token.symbol if token else 'UNKNOWN'

    @classmethod
    async def to_lamport(cls, mint: str, amount: float) -> int:
        token = cls.__temp__.get(mint)
        if not token:
            token = await cls.get_or_none(mint=mint)
            cls.__temp__[mint] = token
        return amount * 10 ** token.decimals if token else 0

    @classmethod
    async def to_amount(cls, mint: str, lamport: int, default=9) -> float:
        token = cls.__temp__.get(mint)
        if not token:
            token = await cls.get_or_none(mint=mint)
            cls.__temp__[mint] = token
        decimals = token.decimals if (token and 16 > token.decimals > 0) else 9
        amount = lamport // (10 ** decimals)
        return amount

    class Meta:
        table = 'token'
