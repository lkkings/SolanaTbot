# # -*- coding: utf-8 -*-
# """
# @Description:
# @Date       : 2024/9/28 3:51
# @Author     : lkkings
# @FileName:  : 转帐测试.py
# @Github     : https://github.com/lkkings
# @Mail       : lkkings888@gmail.com
# -------------------------------------------------
# Change Log  :
#
# """
import asyncio

from solana.rpc.commitment import Confirmed
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from spl.token.async_client import AsyncToken
from clients.rpc import connection
from wallet import Wallet


async def main():
    wallet = Wallet.local()
    await connection.initialize()
    await wallet.initialize()
    instruction = wallet.transfer(wallet.get_associated_token_account(
        'So11111111111111111111111111111111111111112'
    ), 100_000_000)
    block_hash_resp = await connection.get_latest_blockhash(commitment=Confirmed)
    block_hash = block_hash_resp.value.blockhash
    msg = MessageV0.try_compile(
        payer=wallet.public_key,
        instructions=[instruction],
        address_lookup_table_accounts=[],
        recent_blockhash=block_hash
    )

    tx = VersionedTransaction(msg, [wallet.payer])
    resp = await connection.send_raw_transaction(bytes(tx))
    print(resp.value.to_json())

if __name__ == '__main__':
    asyncio.run(main())
