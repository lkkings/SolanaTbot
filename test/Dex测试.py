# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/21 20:32
@Author     : lkkings
@FileName:  : Dex测试.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from wallet import Wallet

# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/21 12:49
@Author     : lkkings
@FileName:  : Amm测试.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from solders.pubkey import Pubkey

import asyncio

from core.constants import SwapMode
from core.types.dex import SwapParams, SwapRoute, Market, TradeOutputOverride
from dex.raydium import raydium
from clients.rpc import connection
from dex.loader import dex_loader
from core.worker import worker

wallet = Wallet.local()
dex_loader.dexs.append(raydium)
dex_loader.bind_wallet(wallet)
if __name__ == '__main__':
    async def test():
        await worker.start()
        await connection.initialize()
        await dex_loader.initialize()
        pool_id = '58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2'
        market = dex_loader.get_market(pool_id)
        account, tx_ = wallet.create_associated_token_account(
            Pubkey.from_string('So11111111111111111111111111111111111111112')
        )
        account2, tx2_ = wallet.create_associated_token_account(
            Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')
        )
        a = await dex_loader.build_swap_route_instruction(
            [SwapRoute(
                market=market,
                fromA=True,
                trade_output_override=TradeOutputOverride(
                    in_=1_000_000_000,
                    estimated_out=1_000_000_000
                )
            )],
            in_amount=1_000_000_000,
            min_out_amount=1_000_000_000
        )
        await dex_loader.close()
        await connection.close()
        await worker.stop()


    asyncio.run(test())
