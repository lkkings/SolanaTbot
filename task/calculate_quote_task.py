# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/7 20:07
@Author     : lkkings
@FileName:  : calculate_quote_task.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from dataclasses import dataclass

from solders.pubkey import Pubkey

from core.base_task import TaskParams, AsyncTask, TaskReq, TaskResp, TaskPayload, V
from core.constants import SwapMode
from core.types.dex import QuoteParams, Quote
from dex.loader import dex_loader
from logger import catch_exceptions


@dataclass
class CalulateQuotePayload(TaskPayload):
    not_enough_liquidity: bool
    min_in_amount: int
    min_out_amount: int
    in_amount: int
    out_amount: int
    fee_amount: int
    fee_mint: Pubkey
    fee_pct: float
    price_impact_pct: float


@dataclass
class CalulateQuoteParams(TaskParams):
    pool_id: Pubkey
    source_mint: Pubkey
    destination_mint: Pubkey
    amount: int
    swap_mode: SwapMode


class CalculateQuoteTask(AsyncTask[V]):

    @catch_exceptions(option='获取报价')
    async def run(self, params: CalulateQuoteParams) -> CalulateQuotePayload:
        amm = dex_loader.get_pool(params.pool_id)
        if not amm:
            raise Exception(f'交易池{params.pool_id}未发现')
        if not amm.is_initialized:
            raise Exception(f'交易池{params.pool_id}未完全初始化')
        quote = amm.get_quote(quote_params=QuoteParams(
            source_mint=params.source_mint,
            destination_mint=params.destination_mint,
            amount=params.amount,
            swap_mode=params.swap_mode
        ))
        return CalulateQuotePayload(
            not_enough_liquidity=quote.not_enough_liquidity,
            min_in_amount=quote.min_in_amount,
            min_out_amount=quote.min_out_amount,
            in_amount=quote.in_amount,
            out_amount=quote.min_out_amount,
            fee_amount=quote.fee_mint,
            fee_mint=quote.fee_mint,
            fee_pct=quote.fee_pct,
            price_impact_pct=quote.price_impact_pct
        )
