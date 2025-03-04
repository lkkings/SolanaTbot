# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/30 20:19
@Author     : lkkings
@FileName:  : OrderArbBot.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
import os
from typing import List

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from rich.markup import escape
from solders.hash import Hash
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.message import MessageV0
from solders.transaction import VersionedTransaction

from clients.jito import jito_client
from clients.jupiter import jupiter_client
from clients.rpc import connection
from core.constants import JITO, BASE_MINT, TARGET_MINT
from dex.lookup_table_provider import lookup_table_provider
from flashloan import flashloan
from logger import logger
from utils.console_manager import ConsoleManager
from wallet import Wallet
from db import DB
from db.model import Token

console = Console()


async def simulate_arb(instructions: List[Instruction], payer: Keypair, recent_block_hash: Hash):
    simulate_lookup_tables = lookup_table_provider.compute_ideal_lookup_tables_for_instructions(
        instructions
    )
    simulate_message = MessageV0.try_compile(
        payer=payer.pubkey(),
        recent_blockhash=recent_block_hash,
        instructions=instructions,
        address_lookup_table_accounts=simulate_lookup_tables
    )
    simulate_tx = VersionedTransaction(
        message=simulate_message,
        keypairs=[payer]
    )
    simulate_tx_bytes = bytes(simulate_tx)
    if len(simulate_tx_bytes) < 1232:
        try:
            simulate_resp = await connection.simulate_transaction(
                simulate_tx
            )
            if simulate_resp.value.err:
                panel = Panel(
                    Text(escape('Simulate Error Log'), style="bold magenta"),
                    expand=False,
                    title='Simulate Error Log',
                    title_align="left",
                    border_style="red"
                )
                logs = [i for i in simulate_resp.value.logs[-10:]]
                panel.renderable = Text('\n'.join(logs))
                console.print(panel)
            else:
                logger.info('交易成功')
        except Exception as e:
            logger.error(f'模拟交易失败=>{e}')

    else:
        logger.warning(f'交易包太大无法模拟=>{len(simulate_tx_bytes)}')


async def main():
    # base_mint = Prompt.ask("请输入内容",default=str(BASE_MINT))
    # BASE_MINT = input(f'请输入 BASE MINT:') or BASE_MINT
    utilization_rate = 0.9
    in_amount = 1_000_000_000
    private_key = os.getenv('PRIVATE_KEY')
    storage_account = os.getenv('MAIN_WALLET')
    storage_account = Pubkey.from_string(storage_account)
    wallet = Wallet.load_from_key(private_key)
    await DB.initialize()
    symbol1 = await Token.get_symbol(str(BASE_MINT))
    symbol2 = await Token.get_symbol(str(TARGET_MINT))
    logger.info(f'套利路线 {symbol1} => {symbol2}')
    await connection.initialize()
    await wallet.initialize()
    await jupiter_client.initialize()
    # await jito_client.initialize()
    # await lookup_table_provider.initialize()
    token_account = wallet.get_associated_token_account(str(BASE_MINT))
    assert token_account, f'不存在{BASE_MINT}的Token账户，请先创建账户！'
    flash_borrow_instruction, flash_repay_instruction = \
        await flashloan.simulate(in_amount, token_account, wallet.payer, connection)
    flash_loan_free = flashloan.get_fee(in_amount)
    min_gas_fee_amount = JITO.FEES_LAMPORTS + JITO.FEES_LAMPORTS
    gas_value = jupiter_client.sol_2_base_mint(min_gas_fee_amount)
    min_out_amount = in_amount + gas_value + flash_loan_free
    logger.info(f'套利额度 {in_amount:.1f} {symbol1}')
    logger.info(f'最低输出 {min_out_amount} {symbol1}')
    await jupiter_client.create_order(
        str(BASE_MINT), str(TARGET_MINT), in_amount, 1000000, owner=str(wallet.payer)
    )


asyncio.run(main())
