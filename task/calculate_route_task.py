# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/8 22:43
@Author     : lkkings
@FileName:  : calculate_route_task.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from dataclasses import dataclass
from typing import Optional

from solders.pubkey import Pubkey

from core.base_task import AsyncTask, V, TaskPayload, TaskParams
from logger import catch_exceptions, logger


@dataclass
class TradeOutputOverride:
    in_: int
    estimated_out: int


@dataclass
class CalculateRouteParams(TaskParams):
    source_mint: Pubkey
    destination_mint: Pubkey
    amount: int
    market_id: Pubkey
    trade_output_override: Optional[TradeOutputOverride]


@dataclass
class CalculateRoutePayload(TaskPayload):
    pass


class CalculateRouteTask(AsyncTask[V]):
    @catch_exceptions(option='计算路由')
    async def run(self, params: CalculateRouteParams) -> CalculateRoutePayload:
        logger.debug(f'计算路由')

