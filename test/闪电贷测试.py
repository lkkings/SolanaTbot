# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/28 4:01
@Author     : lkkings
@FileName:  : 闪电贷测试.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio

from solders.message import MessageV0
from solders.transaction import VersionedTransaction

from clients.rpc import connection
from core.constants import BASE_MINT
from flashloan import flashloan
from logger import logger
from wallet import Wallet


async def main():
    in_amount = 10_000_000_000
    wallet = Wallet.local()
    await connection.initialize()
    await wallet.initialize()
    base_token_account = wallet.get_associated_token_account(str(BASE_MINT))

    flash_borrow_instruction = flashloan.create_borrow_instruction(
        in_amount, base_token_account
    )
    flash_repay_instruction = flashloan.create_repay_instruction(
        in_amount, base_token_account, wallet.public_key
    )

    recent_block_hash_resp = await connection.get_latest_blockhash()
    recent_block_hash = recent_block_hash_resp.value.blockhash
    simulate_instructions = [flash_borrow_instruction,flash_repay_instruction]
    simulate_message = MessageV0.try_compile(
        payer=wallet.public_key,
        recent_blockhash=recent_block_hash,
        instructions=simulate_instructions,
        address_lookup_table_accounts=[]
    )
    simulate_tx = VersionedTransaction(
        message=simulate_message,
        keypairs=[wallet.payer]
    )
    simulate_resp = await connection.simulate_transaction(
        simulate_tx
    )
    simulate = simulate_resp.value
    if simulate.err:
        logger.error('\n'.join(simulate.logs))
    else:
        logger.info(f'交易成功:{simulate}')


"""
Program So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo invoke UTABCRXirrbpCNDogCoqEECtM3V44jXGCsK23ZepV3Z
Program log: Instruction: Flash Borrow Reserve Liquidity
Program TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA invoke 5cSfC32xBUYqGfkURLGfANuK64naHmMp27jUT7LQSujY
Program log: Instruction: Transfer
Program TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA consumed 4736 of 362259 compute units
Program TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA success
Program So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo consumed 42868 of 400000 compute units
Program So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo success
Program So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo invoke UTABCRXirrbpCNDogCoqEECtM3V44jXGCsK23ZepV3Z
Program log: Instruction: Flash Repay Reserve Liquidity
Program TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA invoke 5cSfC32xBUYqGfkURLGfANuK64naHmMp27jUT7LQSujY
Program log: Instruction: Transfer
Program TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA consumed 4736 of 338857 compute units
Program TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA success
Program TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA invoke 5cSfC32xBUYqGfkURLGfANuK64naHmMp27jUT7LQSujY
Program log: Instruction: Transfer
Program log: Error: insufficient funds
Program TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA consumed 4205 of 330893 compute units
Program TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA failed: custom program error: 0x1
Program So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo consumed 30444 of 357132 compute units
Program So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo failed: custom program error: 0x1

"""

if __name__ == '__main__':
    asyncio.run(main())