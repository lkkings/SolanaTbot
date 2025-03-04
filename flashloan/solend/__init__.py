# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/3 22:15
@Author     : lkkings
@FileName:  : __init__.py.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from typing import Tuple

from solders.instruction import Instruction
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solders.transaction import VersionedTransaction

from core.base_flashloan import FlashLoan
from core.constants import SOLEND
from flashloan.solend.instructions import LendingInstruction, build_flash_borrow_instruction, \
    build_flash_repay_instruction
from flashloan.solend.layouts import BORROW_LAYOUT, REPAY_LAYOUT
from logger import logger


class SolendFlashLoan(FlashLoan):
    def create_borrow_instruction(self, amount: int, token_account: Pubkey) -> Instruction:
        return build_flash_borrow_instruction(
            liquidity_amount=amount,
            source_liquidity=SOLEND.LIQUIDITY,
            destination_liquidity=token_account,
            reserve=SOLEND.RESERVE,
            lending_market=SOLEND.POOL,
            lending_program_id=SOLEND.PROGRAM_ID
        )

    def create_repay_instruction(self, amount: int, token_account: Pubkey,
                                 user_transfer_authority: Pubkey) -> Instruction:
        return build_flash_repay_instruction(
            liquidity_amount=amount,
            borrow_instruction_index=0,
            source_liquidity=token_account,
            destination_liquidity=SOLEND.LIQUIDITY,
            reserve_liquidity_fee_receiver=SOLEND.FEE_RECEIVER,
            host_fee_receiver=token_account,
            reserve=SOLEND.RESERVE,
            lending_market=SOLEND.POOL,
            user_transfer_authority=user_transfer_authority,
            lending_program_id=SOLEND.PROGRAM_ID
        )

    def get_fee(self, in_amount: int) -> int:
        return int(in_amount * SOLEND.FLASHLOAN_FEE_BPS / 10000)

    async def simulate(self, amount, token_account: Pubkey, payer: Keypair, con: AsyncClient) -> Tuple[Instruction,Instruction]:
        flash_borrow_instruction = self.create_borrow_instruction(
            amount, token_account
        )
        flash_repay_instruction = self.create_repay_instruction(
            amount, token_account, payer.pubkey()
        )
        recent_block_hash_resp = await con.get_latest_blockhash()
        recent_block_hash = recent_block_hash_resp.value.blockhash
        simulate_instructions = [flash_borrow_instruction, flash_repay_instruction]
        simulate_message = MessageV0.try_compile(
            payer=payer.pubkey(),
            recent_blockhash=recent_block_hash,
            instructions=simulate_instructions,
            address_lookup_table_accounts=[]
        )
        simulate_tx = VersionedTransaction(
            message=simulate_message,
            keypairs=[payer]
        )
        simulate_resp = await con.simulate_transaction(
            simulate_tx
        )
        simulate = simulate_resp.value
        if simulate.err:
            logger.error('\n'.join(simulate.logs))
            raise Exception('闪电贷执行异常')
        else:
            logger.info('闪电贷交易模拟通过')
            return flash_borrow_instruction, flash_repay_instruction
