# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/15 16:12
@Author     : lkkings
@FileName:  : 更新Pool和Token.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from db import DB

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


async def update_raydium():
    await DB.initialize()

    async def do(page):
        params = {
            'poolType': 'standard',
            'poolSortField': 'liquidity',
            'sortType': 'desc',
            'pageSize': '100',
            'page': str(page),
        }
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    resp = await session.get(
                        'https://api-v3.raydium.io/pools/info/list',
                        params=params,
                        proxy='http://127.0.0.1:7890',
                        headers={
                            'accept': 'application/json',
                        }
                    )
                    data = (await resp.json())['data']['data']
                    return data
            except Exception as e:
                await asyncio.sleep(5)

    pools_info = {}
    results, _ = await asyncio.wait([do(page) for page in range(1, 50)])
    for result in results:
        _pools = result.result()
        for _pool in _pools:
            token = _pool['mintA']
            mint_a = {
                'symbol': token['symbol'],
                'name': token['name'],
                'decimals': token['decimals'],
                'mint': token['address'],
                'extensions': json.dumps(token['extensions']),
                'icon': token['logoURI'],
                'hasFreeze': token['tags'][0] if token['tags'] else 0
            }
            token = _pool['mintB']
            mint_b = {
                'symbol': token['symbol'],
                'name': token['name'],
                'decimals': token['decimals'],
                'mint': token['address'],
                'extensions': json.dumps(token['extensions']),
                'icon': token['logoURI'],
                'hasFreeze': token['tags'][0] if token['tags'] else 0
            }
            pools_info[_pool['id']] = {
                'baseMintAmount': _pool['mintAmountA'],
                'quoteMintAmount': _pool['mintAmountB'],
                'fee_rate_bps': _pool['feeRate'] * 10000
            }
            try:
                await Token.update_or_create(**mint_a)
            except Exception as e:
                print(e)
            try:
                await Token.update_or_create(**mint_b)
            except Exception as e:
                print(e)

    with open(f'D:\Project\Python\SolanaTbot\data\mainnet.json') as f:
        data = json.load(f)
    _official_pools = data['official']
    official_pools = []
    for pool in _official_pools:
        if pool['id'] in pools_info:
            pool.update(pools_info[pool['id']])
            official_pools.append(pool)
            print(pool)
    _unofficial_pools = data['unOfficial']
    unofficial_pools = []
    for pool in _unofficial_pools:
        if pool['id'] in pools_info:
            pool.update(pools_info[pool['id']])
            unofficial_pools.append(pool)
            print(pool)
    with open('mainnet.json', 'w') as f:
        f.write(json.dumps({
            'official': official_pools,
            'unOfficial': unofficial_pools,
        }))


if __name__ == '__main__':
    asyncio.run(update_raydium())
