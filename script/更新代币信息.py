# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/15 15:40
@Author     : lkkings
@FileName:  : 更新代币信息.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
import json

import aiohttp

from db import DB
from db.model import Token


async def update():
    await DB.initialize()
    i = 0
    async with aiohttp.ClientSession() as session:
        resp = await session.get('https://api.raydium.io/v2/sdk/token/raydium.mainnet.json', proxy='http://127.0.0.1:7890')
        data = await resp.json()
    tokens = data['official']
    tokens.extend(data['unOfficial'])
    with open(r'D:\Project\Python\SolanaTbot\data\token.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False))
    for item in tokens:
        try:
            await Token.update_or_create(**item)
            i += 1
            print(item)
        except Exception as e:
            print(e)
            pass
    print(i)
    await DB.close()

if __name__ == '__main__':
    asyncio.run(update())