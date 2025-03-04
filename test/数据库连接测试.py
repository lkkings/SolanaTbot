# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/19 21:49
@Author     : lkkings
@FileName:  : 数据库连接测试.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio

from db import DB
from db.model import Token

if __name__ == '__main__':
    async def test():
        await DB.initialize()
        tokens = await Token.get_or_none(mint='GinNabffZL4fUj9Vactxha74GDAW8kDPGaHqMtMzps2f')
        print(tokens)
        await DB.close()

    asyncio.run(test())