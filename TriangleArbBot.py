# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/26 0:11
@Author     : lkkings
@FileName:  : TriangleArbBot.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
import os
import traceback
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
    in_amount = int(Prompt.ask("请输入套利额度"))
    private_key = Prompt.ask("请输入支付密匙", password=True)
    storage_account = Prompt.ask("请输入存储账户", default=os.getenv('MAIN_WALLET'))
    storage_account = Pubkey.from_string(storage_account)
    wallet = Wallet.load_from_key(private_key)
    await DB.initialize()
    symbol1 = await Token.get_symbol(str(BASE_MINT))
    symbol2 = await Token.get_symbol(str(TARGET_MINT))
    logger.info(f'套利路线 {symbol1} => {symbol2}')
    await connection.initialize()
    await wallet.initialize()
    await jupiter_client.initialize()
    await jito_client.initialize()
    await lookup_table_provider.initialize()
    token_account = wallet.get_associated_token_account(str(BASE_MINT))
    assert token_account, f'不存在{BASE_MINT}的Token账户，请先创建账户！'
    flash_borrow_instruction, flash_repay_instruction = \
        await flashloan.simulate(in_amount, token_account, wallet.payer, connection)
    flash_loan_free = flashloan.get_fee(in_amount)
    utilization_rate = min(1, utilization_rate)
    ConsoleManager.print_table(
        ['支出', '数额', '代币'],
        [
            ['闪电贷', f'{flash_loan_free:.1f}', f'{symbol1}'],
            ['Jito燃油费', f'{JITO.FEES_LAMPORTS:.1f}', 'SOL'],
            ['Jito基础小费', f'{JITO.MIN_TIP_LAMPORTS:.1f}', 'SOL']
        ]
    )
    gas_value = jupiter_client.sol_2_base_mint(JITO.FEES_LAMPORTS)
    min_tip_value = jupiter_client.sol_2_base_mint(JITO.MIN_TIP_LAMPORTS)
    min_out_amount = in_amount + gas_value + flash_loan_free + min_tip_value
    logger.info(f'套利额度 {in_amount:.1f} {symbol1}')
    logger.info(f'最低输出 {min_out_amount} {symbol1}')
    Prompt.ask("请确认以上信息！")
    while True:
        try:
            await asyncio.sleep(1)
            routes = []
            i = 0
            buy_amount = int(in_amount * utilization_rate)
            routes.append([str(i), symbol1, str(buy_amount)])
            buy_resp = await jupiter_client.quote(
                input_mint=str(BASE_MINT),
                output_mint=str(TARGET_MINT),
                amount=in_amount,
                slippage_bps=100,
            )
            sell_amount = int(buy_resp['outAmount'])
            sell_resp = await jupiter_client.quote(
                input_mint=str(TARGET_MINT),
                output_mint=str(BASE_MINT),
                amount=sell_amount,
                slippage_bps=100,
            )
            _routes = [*buy_resp['routePlan'], *sell_resp['routePlan']]
            for route in _routes:
                i += 1
                swap_info = route['swapInfo']
                token = await Token.get_symbol(swap_info['outputMint'])
                routes.append([str(i), token, swap_info['outAmount']])
            out_amount = int(sell_resp['outAmount']) + (1 - utilization_rate) * in_amount
            expected_profit = int(out_amount - min_out_amount)
            extra_tip_amount = max(JITO.MIN_TIP_LAMPORTS, jupiter_client.base_mint_2_sol(
                expected_profit * JITO.TIP_PERCENT
            )) - JITO.MIN_TIP_LAMPORTS
            tip_amount = JITO.MIN_TIP_LAMPORTS + extra_tip_amount
            profit = expected_profit - jupiter_client.sol_2_base_mint(expected_profit)
            get_swap_task = asyncio.create_task(
                jupiter_client.multiple_swap(
                    quote_responses=[buy_resp, sell_resp],
                    payer=wallet.public_key,
                    wrap_and_unwrap_sol=False
                )
            )
            get_recent_block_hash_task = asyncio.create_task(
                connection.get_recent_block_hash()
            )
            down_tasks, _ = await asyncio.wait([get_swap_task, get_recent_block_hash_task])
            recent_block_hash, swap_resp = None, None
            for task in down_tasks:
                result = task.result()
                if isinstance(result, Hash):
                    recent_block_hash = result
                else:
                    swap_resp = result
            [buy_instructions, sell_instructions], address_lookup_table_addresses = swap_resp
            await lookup_table_provider.batch_update(address_lookup_table_addresses)

            step1_instructions = [
                flash_borrow_instruction,
            ]
            step2_instructions = [
                *buy_instructions
            ]
            step3_instructions = [
                *sell_instructions
            ]
            step4_instructions = [
                flash_repay_instruction
            ]
            tip_instruction = wallet.transfer(jito_client.tip_account, tip_amount)
            storage_amount = max(int(profit * 0.8), jupiter_client.sol_2_base_mint(tip_amount + JITO.FEES_LAMPORTS))
            storage_instruction = wallet.transfer(storage_account, storage_amount)
            step5_instructions = [
                storage_instruction,
                tip_instruction
            ]

            step1_lookup_tables = lookup_table_provider.compute_ideal_lookup_tables_for_instructions(
                step1_instructions
            )
            step2_lookup_tables = lookup_table_provider.compute_ideal_lookup_tables_for_instructions(
                step2_instructions
            )
            step3_lookup_tables = lookup_table_provider.compute_ideal_lookup_tables_for_instructions(
                step3_instructions
            )
            step4_lookup_tables = lookup_table_provider.compute_ideal_lookup_tables_for_instructions(
                step4_instructions
            )
            step5_lookup_tables = lookup_table_provider.compute_ideal_lookup_tables_for_instructions(
                step5_instructions
            )

            step1_message = MessageV0.try_compile(
                payer=wallet.public_key,
                recent_blockhash=recent_block_hash,
                instructions=step1_instructions,
                address_lookup_table_accounts=step1_lookup_tables
            )
            step2_message = MessageV0.try_compile(
                payer=wallet.public_key,
                recent_blockhash=recent_block_hash,
                instructions=step2_instructions,
                address_lookup_table_accounts=step2_lookup_tables
            )
            step3_message = MessageV0.try_compile(
                payer=wallet.public_key,
                recent_blockhash=recent_block_hash,
                instructions=step3_instructions,
                address_lookup_table_accounts=step3_lookup_tables
            )
            step4_message = MessageV0.try_compile(
                payer=wallet.public_key,
                recent_blockhash=recent_block_hash,
                instructions=step4_instructions,
                address_lookup_table_accounts=step4_lookup_tables
            )
            step5_message = MessageV0.try_compile(
                payer=wallet.public_key,
                recent_blockhash=recent_block_hash,
                instructions=step5_instructions,
                address_lookup_table_accounts=step5_lookup_tables
            )

            step1_tx = VersionedTransaction(
                message=step1_message,
                keypairs=[wallet.payer]
            )
            step2_tx = VersionedTransaction(
                message=step2_message,
                keypairs=[wallet.payer]
            )
            step3_tx = VersionedTransaction(
                message=step3_message,
                keypairs=[wallet.payer]
            )
            step4_tx = VersionedTransaction(
                message=step4_message,
                keypairs=[wallet.payer]
            )
            step5_tx = VersionedTransaction(
                message=step5_message,
                keypairs=[wallet.payer]
            )
            simulate_instructions = [
                *step1_instructions,
                *step2_instructions,
                *step3_instructions,
                *step4_instructions,
                *step5_instructions
            ]
            simulate_task = asyncio.create_task(
                simulate_arb(simulate_instructions, wallet.payer, recent_block_hash)
            )
            ConsoleManager.print_table(['Step', '代币', '数额'], routes)
            profit_amount = await Token.to_amount(str(BASE_MINT), profit)
            logger.info(f'预计收益: {profit_amount:.6f}{symbol1} 燃油费:'
                        f'{JITO.FEES_LAMPORTS / 10 ** 9:.6f}SOL '
                        f'小费: {tip_amount / 10 ** 9:.6f}SOL ')
            bundle_id = await jito_client.send_bundle(
                [step1_tx, step2_tx, step3_tx, step4_tx, step5_tx]
            )
            await jito_client.wait_down(bundle_id)

        except Exception as e:
            traceback.print_exc()
            logger.error(e)


asyncio.run(main())
