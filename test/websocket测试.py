# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/8/22 2:01
@Author     : lkkings
@FileName:  : websocket测试.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import json
import asyncio
from solders.keypair import Keypair
from solana.rpc.websocket_api import connect
from solders.pubkey import Pubkey

with open('main-wallet-data.json', mode='r', encoding='utf-8') as f:
    wallet = json.load(f)

public_key = Pubkey.from_string(wallet['public_key'])
wallet = Keypair.from_bytes(wallet['secret_key'])
async def main():
    async with connect("wss://api.devnet.solana.com") as websocket:
        # Subscribe to the Test wallet-data to listen for events
        await websocket.account_subscribe(wallet.pubkey())
        # Capture response from account subscription
        first_resp = await websocket.recv()
        print("Subscription successful with id {}, listening for events \n".format(first_resp))
        updated_account_info = await websocket.recv()
        print(updated_account_info)


asyncio.run(main())