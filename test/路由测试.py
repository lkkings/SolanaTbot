# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/16 23:37
@Author     : lkkings
@FileName:  : 路由测试.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from dex.loader import dex_loader

if __name__ == '__main__':
    import asyncio
    from clients.rpc import connection
    from dex.raydium import raydium
    from core.worker import worker


    async def test():
        await worker.start()
        await connection.initialize()
        dex_loader.dexs.append(raydium)
        await dex_loader.initialize()
        a = dex_loader.get_most_height_value_route('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v','ATLASXmbPQxBUYbxPsV97usA3fPQYEqzQBUHgiFCUsXx', 1_000_000_000)
        b = dex_loader.get_most_low_value_route('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v','ATLASXmbPQxBUYbxPsV97usA3fPQYEqzQBUHgiFCUsXx', 1_000_000_000)

        c = dex_loader.get_most_height_value_route('ATLASXmbPQxBUYbxPsV97usA3fPQYEqzQBUHgiFCUsXx','EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', a[-1].trade_output_override.estimated_out)
        d = dex_loader.get_most_low_value_route('ATLASXmbPQxBUYbxPsV97usA3fPQYEqzQBUHgiFCUsXx','EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', a[-1].trade_output_override.estimated_out)
        print('===================================')
        print(a)
        print('====================================')
        print(b)
        print('====================================')
        print(c)
        print('====================================')
        print(d)
        await worker.stop()


    asyncio.run(test())
