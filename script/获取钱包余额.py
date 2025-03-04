import asyncio
import json

from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey

with open('../wallet-data/test-wallet-01.json', mode='r', encoding='utf-8') as f:
    wallet = Keypair.from_bytes(json.load(f))

# 399990000
async def main():
    async with AsyncClient("https://api.testnet.solana.com") as client:
        if await client.is_connected():
            print('连接成功')
        else:
            raise Exception('连接失败')
        # 获取账户余额
        balance = await client.get_balance(wallet.pubkey())
        # 打印余额
        print(f"Balance: {balance.value}")

asyncio.run(main())