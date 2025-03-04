# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/7 20:24
@Author     : lkkings
@FileName:  : add_pool_task.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from dataclasses import dataclass
from typing import List, Optional
from solders.pubkey import Pubkey

from core.base_amm import Amm
from core.base_task import TaskParams, AsyncTask, TaskReq, TaskResp, TaskPayload, V
from core.constants import DexLabel
from core.types.dex import SerumMarketKeysString, AccountInfo
from dex.orca.amm import OrcaAmm
from dex.raydium.amm import RaydiumAmm
from logger import logger, catch_exceptions


@dataclass
class AddPoolParams(TaskParams):
    pool_label: DexLabel
    pool_id: Pubkey
    fee_rate_bps: int
    account_info: AccountInfo
    serum_params: Optional[SerumMarketKeysString] = None


@dataclass
class AddPoolPayload(TaskPayload):
    amm: Amm


class AddPoolTask(AsyncTask[V]):
    @catch_exceptions(option='添加交易池')
    async def run(self, params: AddPoolParams) -> AddPoolPayload:
        account_info = params.account_info
        pool_label = params.pool_label
        logger.debug(f'添加Pool[{params.pool_label.value}] => {params.pool_id}')
        serumParams = params.serum_params
        if pool_label == DexLabel.RAYDIUM:
            if not serumParams:
                raise Exception('未提供 Raydium 池的 Serum 参数')
            amm = RaydiumAmm(params.pool_id, account_info, serumParams)
        if pool_label == DexLabel.ORCA:
            amm = OrcaAmm(params.pool_id, account_info, 'Orca')
        else:
            raise Exception(f'未知池 {pool_label.value}')
        amm.is_initialized = len(amm.accounts_for_update) == 0
        amm.fee_rate_bps = params.fee_rate_bps
        return AddPoolPayload(amm=amm)
