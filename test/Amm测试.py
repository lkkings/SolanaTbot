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

from core.constants import SwapMode
from core.types.dex import SwapParams
from dex.raydium import RaydiumAmm, decode_serum_market_keys_string

if __name__ == '__main__':
    from clients.rpc import connection
    import asyncio


    async def test():
        await connection.initialize()
        pool_id = Pubkey.from_string('58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2')
        pool_account_info_resp = await connection.get_account_info(pool_id)
        pool_account_info = pool_account_info_resp.value
        market_id = Pubkey.from_string('8BnEgHoWFysVcuFFX7QztDmzuH8r5ZFvyP3sYwn1XTh6')
        market_account_info_resp = await connection.get_account_info_json_parsed(market_id)
        market_account_info = market_account_info_resp.value
        print(str(market_account_info.data[-7:]))
        serum_params = decode_serum_market_keys_string(
            pool_id,
            Pubkey.from_string('srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX'),
            market_id,
            market_account_info
        )
        amm = RaydiumAmm(pool_id, pool_account_info, serum_params)
        data = {}

        async def a(s):
            resp = await connection.get_account_info(Pubkey.from_string(s))
            data[s] = resp.value

        for i in amm.accounts_for_update:
            await a(i)
        amm.update(data)
        m = amm.get_swap_leg_and_accounts(
            SwapParams(
                source_mint=Pubkey.from_string('So11111111111111111111111111111111111111112'),
                destination_mint=Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'),
                user_source_token_account= Pubkey.from_string('DQyrAcCrDXQ7NeoqGgDCZwBvWDcYmFCjSb9JtteuvPpz'),
                user_destination_token_account=Pubkey.from_string('HLmqeL62xR1QoZ1HKKbXRrdN1p3phKpxRMb2VVopvBBz'),
                user_transfer_authority=Pubkey.from_string('CTz5UMLQm2SRWHzQnU62Pi4yJqbNGjgRBHqqp6oDHfF7'),
                amount=1_000_000,
                swap_mode=SwapMode.ExactIn,
                open_orders_address=None,
                quote_mint_to_referrer=None
            )
        )
        print(m[0].__dict__)
        await connection.close()


    asyncio.run(test())