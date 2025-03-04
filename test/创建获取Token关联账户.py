# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/17 1:38
@Author     : lkkings
@FileName:  : 创建获取Token关联账户.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
import json

from solana.rpc.commitment import Processed, Confirmed
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from solders.system_program import create_account
from spl.token.constants import WRAPPED_SOL_MINT

from clients.rpc import AsyncConnection, connection
from core.constants import BASE_MINT
from wallet import Wallet


# def get_token_account(owner: Pubkey.from_string,
#                       mint: Pubkey.from_string):
#     try:
#         account_data = ctx.get_token_accounts_by_owner(owner, TokenAccountOpts(mint))
#         return account_data.value[0].pubkey, None
#     except:
#         swap_associated_token_address = get_associated_token_address(owner, mint)
#         swap_token_account_Instructions = create_associated_token_account(owner, owner, mint)
#         return swap_associated_token_address, swap_token_account_Instructions
#

async def test():
    await connection.initialize()

    mainnet_wallet = Wallet.local()
    await mainnet_wallet.get_balance()
    await mainnet_wallet.initialize()
    instruction = mainnet_wallet.create_associated_token_account(str(BASE_MINT))
    # mint = Pubkey.from_string('AjMpnWhqrbFPJTQps4wEPNnGuQPMKUcfqHUqAeEf1WM4')
    # a, b = devnet_wallet.create_associated_token_account(mint)
    # c = devnet_wallet.close_associated_token_account(mint)
    block_hash = await connection.get_latest_blockhash(commitment=Confirmed)
    msg = MessageV0.try_compile(
        payer=mainnet_wallet.public_key,
        instructions=[instruction],
        address_lookup_table_accounts=[],
        recent_blockhash=block_hash.value.blockhash,
    )

    tx = VersionedTransaction(msg, [mainnet_wallet.payer])
    resp = await connection.send_raw_transaction(bytes(tx))
    print(resp.value.to_json())

if __name__ == '__main__':
    asyncio.run(test())
