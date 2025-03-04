# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/9 1:05
@Author     : lkkings
@FileName:  : Raydium测试.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request

from clients.rpc import connection
from clients.jito import jito_client
from db import DB
from clients.helius import helius_client
from dex.raydium import raydium
from dex.loader import dex_loader
from core.worker import worker
from strategy import triangle_strategy as strategy
from wallet import Wallet

dex_loader.dexs.append(raydium)
dex_loader.bind_wallet(Wallet.local())


@asynccontextmanager
async def lifespan(app: FastAPI):
    await DB.initialize()
    await worker.start()
    await jito_client.initialize()
    await connection.initialize()
    await helius_client.initialize()
    await dex_loader.initialize()
    await strategy.start()
    yield
    await strategy.stop()
    await dex_loader.close()
    await helius_client.close()
    await connection.close()
    await jito_client.close()
    await worker.stop()
    await DB.close()


app = FastAPI(lifespan=lifespan)


@app.post('/webhook')
async def webhook(request: Request):
    data = await request.json()
    await strategy.pre_execute(data)
    # await triangle_strategy.pre_execute(data)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8888, log_config=None)
