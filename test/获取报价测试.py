# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/11 23:19
@Author     : lkkings
@FileName:  : 获取报价测试.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio

from spl.token.instructions import InitializeAccountParams

from clients.rpc import connection
from core.worker import worker
from core.constants import TOKEN, SwapMode
from db import DB
from dex.loader import dex_loader
from dex.raydium import raydium
from logger import logger
from task import CalculateQuoteTask, CalulateQuotePayload, CalulateQuoteParams
from solders.system_program import create_account, CreateAccountParams


class TradeBot:
    async def boot(self):
        await DB.initialize()
        await worker.start()
        await connection.initialize()
        dex_loader.dexs.append(raydium)
        await dex_loader.initialize()
        USTD2SOL_MARKET = dex_loader.get_markets_for_pair(
            str(TOKEN.SOL.mint), str(TOKEN.USTC.mint)
        )
        assert len(USTD2SOL_MARKET) > 0, f'未发现交易对 {TOKEN.SOL.symbol}/{TOKEN.USTC.symbol}'
        resp = await worker.run_task(
            CalculateQuoteTask[CalulateQuotePayload](
                CalulateQuoteParams(
                    pool_id=USTD2SOL_MARKET[0].id,
                    source_mint=TOKEN.USTC.mint,
                    destination_mint=TOKEN.SOL.mint,
                    amount=1000000,
                    swap_mode=SwapMode.ExactIn
                )
            )

        )
        logger.info('===============================')
        logger.info(f'{resp.payload}')
        logger.info(f'==============================')
        await DB.close()

    async def shutdown(self):
        await worker.stop()


asyncio.run(TradeBot().boot())
