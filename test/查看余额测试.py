# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/28 11:38
@Author     : lkkings
@FileName:  : 查看余额测试.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio

from solana.rpc.types import TokenAccountOpts
from spl.token.constants import TOKEN_PROGRAM_ID

from clients.rpc import connection
from wallet import Wallet
async def main():
    wallet = Wallet.local()
    await connection.initialize()
    await wallet.initialize()
    a = await wallet.get_balance()
    print(a)
    b = await connection.get_token_accounts_by_owner_json_parsed(wallet.public_key, TokenAccountOpts(program_id=TOKEN_PROGRAM_ID))
    print(b)
if __name__ == '__main__':
    asyncio.run(main())