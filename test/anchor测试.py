# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/8/24 11:00
@Author     : lkkings
@FileName:  : anchor测试.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
import json

from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey

from core.constants import *
from anchorpy import Program, Provider
from wallet import Wallet




wallet = Wallet.local()


async def main():
    client = AsyncClient("https://api.devnet.solana.com/")
    provider = Provider(client, wallet)
    # load the Serum Swap Program (not the Serum dex itself).
    program_id = Pubkey.from_string("So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo")
    program = await Program.at(
        program_id, provider
    )
    print(program.idl.name)  # swap
    await program.close()


asyncio.run(main())
