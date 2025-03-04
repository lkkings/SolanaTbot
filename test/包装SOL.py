# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/28 14:41
@Author     : lkkings
@FileName:  : 包装SOL.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
import os
from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from spl.token.constants import WRAPPED_SOL_MINT, TOKEN_PROGRAM_ID
from spl.token.async_client import AsyncToken
from spl.token.instructions import sync_native, SyncNativeParams

from clients.rpc import connection
from wallet import Wallet


async def main(amount):
    wallet = Wallet.local()
    await connection.initialize()
    await wallet.initialize()
    # Create the associated token account if it doesn't exist
    spl_client = AsyncToken(connection, WRAPPED_SOL_MINT, TOKEN_PROGRAM_ID, wallet.payer)
    wsol_account = wallet.get_associated_token_account(str(WRAPPED_SOL_MINT))
    # Transfer SOL to the WSOL account
    print("Converting SOL to WSOL...")
    ix1 = wallet.transfer(
        receiver=wsol_account,
        lamports=amount
    )
    ix2 = sync_native(
        SyncNativeParams(
            program_id=TOKEN_PROGRAM_ID,
            account=wsol_account
        )
    )
    block_hash = await connection.get_latest_blockhash(commitment=Confirmed)
    msg = MessageV0.try_compile(
        payer=wallet.public_key,
        instructions=[ix1,ix2],
        address_lookup_table_accounts=[],
        recent_blockhash=block_hash.value.blockhash,
    )

    tx = VersionedTransaction(msg, [wallet.payer])
    resp = await connection.send_raw_transaction(bytes(tx))
    print(resp.value.to_json())
    print(f"Successfully converted {amount} SOL to WSOL.")


# Example usage

asyncio.run(main(10_000))
