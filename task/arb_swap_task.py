# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/17 0:40
@Author     : lkkings
@FileName:  : arb_swap_task.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import os
from dataclasses import dataclass
from typing import List

from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.system_program import create_account, CreateAccountParams
from spl.token.constants import ACCOUNT_LEN, TOKEN_PROGRAM_ID
from spl.token.instructions import initialize_account, InitializeAccountParams

from clients.jito import jito_client
from core.base_task import TaskParams, AsyncTask, TaskPayload, V
from core.constants import TOKEN, JITO
from core.types.dex import SwapRoute
from flashloan import flashloan
from logger import catch_exceptions, logger
from programs import jupiter
from dex.loader import dex_loader


@dataclass
class ArbSwapParams(TaskParams):
    source_mint: str
    destination_mint: str
    amount: int


@dataclass
class ArbSwapPayload(TaskPayload):
    pass


def calculate_min_gas_fee():
    return dex_loader.get_value_mint_amount(str(TOKEN.SOL.mint), JITO.FEES_LAMPORTS + JITO.MIN_TIP_LAMPORTS)


def calculate_expected_profit(in_amount: int, out_amount: int, min_gas_fee: int) -> int:
    return out_amount - in_amount - min_gas_fee - flashloan.get_fee(in_amount)


def calculate_min_out_amount(in_amount: int, min_gas_fee: int) -> int:
    return in_amount + min_gas_fee + flashloan.get_fee(in_amount)


def calculate_tip_lamports(expected_profit: int) -> int:
    return expected_profit * JITO.TIP_PERCENT / 100


class ArbSwapTask(AsyncTask[V]):
    priority = 1

    @catch_exceptions(option='执行套利交易')
    async def run(self, params: ArbSwapParams) -> ArbSwapPayload:

        a_2_b_swap_routes = dex_loader.get_most_height_value_route(params.source_mint, params.destination_mint,
                                                                   amount=params.amount)
        out_amount = a_2_b_swap_routes[-1].trade_output_override.estimated_out
        b_2_a_swap_routes = dex_loader.get_most_height_value_route(params.destination_mint, params.source_mint,
                                                                   out_amount)
        swap_routes: List[SwapRoute] = [*a_2_b_swap_routes, *b_2_a_swap_routes]
        min_gas_fee = calculate_min_gas_fee()
        expected_profit = calculate_expected_profit(params.amount, swap_routes[-1].trade_output_override.estimated_out,
                                                    min_gas_fee)
        logger.info(f'期待收益=>{expected_profit}')
        if expected_profit < 0:
            raise Exception(f'无法套利')

        # 创建中间代币关联账号
        setup_instructions = []
        intermediate_mints = []
        for swap_route in swap_routes:
            intermediate_mints.append(swap_route.market.tokenMintA)
            intermediate_mints.append(swap_route.market.tokenMintB)
        intermediate_mints.remove(params.source_mint)
        for intermediate_mint in intermediate_mints:
            if dex_loader.wallet.get_associated_token_account(intermediate_mint) is None:
                associated_token_account_instruction = dex_loader.wallet.create_associated_token_account(
                    intermediate_mint)
                setup_instructions.append(associated_token_account_instruction)

        main_instructions = []
        source_token_account = dex_loader.wallet.get_associated_token_account(params.source_mint)
        # 借钱
        flash_borrow_instruction = flashloan.create_borrow_instruction(
            params.amount, source_token_account
        )
        main_instructions.append(flash_borrow_instruction)

        # 交换
        swap_leg, remaining_accounts = dex_loader.get_swap_leg_and_accounts(swap_routes)
        accounts = {
            'user_transfer_authority': dex_loader.wallet.public_key,
            'destination_token_account': source_token_account
        }
        min_out_amount = calculate_min_out_amount(params.amount, min_gas_fee)
        swap_instruction = jupiter.build_swap_route_instruction(
            swap_leg=swap_leg,
            accounts=accounts,
            in_amount=params.amount,
            quoted_out_amount=min_out_amount,
            remaining_accounts=remaining_accounts
        )
        main_instructions.append(swap_instruction)

        # 还钱
        flash_repay_instruction = flashloan.create_repay_instruction(
            params.amount, source_token_account, dex_loader.wallet.public_key
        )
        main_instructions.append(flash_repay_instruction)

        # 关闭中间代币关联账号
        for intermediate_mint in intermediate_mints:
            if dex_loader.wallet.get_associated_token_account(intermediate_mint):
                close_token_account_instruction = dex_loader.wallet.close_associated_token_account(
                    intermediate_mint)
                main_instructions.append(close_token_account_instruction)

        # 给小费
        tip_lamports = calculate_tip_lamports(expected_profit)
        tip_instruction = jito_client.create_tip_instruction(
            dex_loader.wallet.public_key, tip_lamports
        )
        main_instructions.append(tip_instruction)
        return ArbSwapPayload()
