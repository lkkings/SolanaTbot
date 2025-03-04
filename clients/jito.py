# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/1 10:01
@Author     : lkkings
@FileName:  : jito.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
import base64
import os
import random
import time
from typing import Dict, List, Union
from urllib.parse import urljoin

import based58
from solders.instruction import Instruction
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams

from core.base_client import Client
from core.constants import JITO
from logger import catch_exceptions, logger
from wallet import TX

BLOCK_ENGINE_URLS = {
    '阿姆斯特丹': 'https://amsterdam.mainnet.block-engine.jito.wtf',
    '法兰克福': 'https://frankfurt.mainnet.block-engine.jito.wtf',
    '纽约': 'https://ny.mainnet.block-engine.jito.wtf',
    '东京': 'https://tokyo.mainnet.block-engine.jito.wtf',
    '盐湖城': 'https://slc.mainnet.block-engine.jito.wtf'
}


class JitoClient(Client):
    """
    api文档参考：https://jito-labs.gitbook.io/mev/searcher-resources/json-rpc-api-reference/bundles
    捆绑交易
    """

    async def initialize(self):
        await super().initialize()
        self._url = await self._get_best_node()
        await self._flush_tip_accounts()
        task = asyncio.create_task(self._flush_tip_accounts_task())
        self._background_tasks.append(task)

    async def _get_best_node(self):
        logger.info(f'正在测试主网区块引擎节点的连通性...')
        best_delay, best_node = float('inf'), None
        for name, url in BLOCK_ENGINE_URLS.items():
            delay = await self.ping(url)
            if delay < best_delay:
                best_node = name
                best_delay = delay
            logger.info(f'{name}=>{url} {delay} ms')
        best_block_engine_url = BLOCK_ENGINE_URLS.get(best_node)
        logger.info(f'选取最佳节点{best_node}=>{best_block_engine_url}')
        return best_block_engine_url

    @property
    def tip_account(self) -> Pubkey:
        return random.choice(self._tip_accounts)

    def create_tip_instruction(self, from_: Pubkey, lamports: int) -> Instruction:
        return transfer(TransferParams(
            from_pubkey=from_,
            to_pubkey=random.choice(self._tip_accounts),
            lamports=lamports
        ))

    async def _flush_tip_accounts(self):
        self._tip_accounts = [Pubkey.from_string(i) for i in await self.get_tip_accounts()]

    async def _flush_tip_accounts_task(self):
        while True:
            await asyncio.sleep(10)
            await self._flush_tip_accounts()

    async def send_rpc_json(self, method: str, params: List, path=None) -> Union[Dict, List, str]:
        headers = {'Content-Type': 'application/json'}
        data = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': method,
            'params': params,
        }
        endpoint_url = urljoin(self._url, '/api/v1/bundles?bundleOnly=true')
        data = await self.make_request(endpoint_url, method='POST', json=data, headers=headers,
                                       proxy=os.getenv('PROXY'))
        try:
            return data['result']
        except KeyError:
            raise Exception(data['error'])

    @catch_exceptions(option='获取飞行中捆绑包状态')
    async def get_inflight_bundle_statuses(self, param: List[str]) -> Dict:
        """
            api文档参考：https://jito-labs.gitbook.io/mev/searcher-resources/json-rpc-api-reference/bundles/getinflightbundlestatuses
        :param param: REQUIRED需要确认的 bundle ID 数组（最多 5 个）
        :return:
        """
        return await self.send_rpc_json('getInflightBundleStatuses', [param])

    @catch_exceptions(option='获取已提交捆绑包状态')
    async def get_bundle_statuses(self, param: List[str]) -> Dict:
        """
            api文档参考：https://jito-labs.gitbook.io/mev/searcher-resources/json-rpc-api-reference/bundles/getbundlestatuses
        :param param: REQUIRED需要确认的 bundle ID 数组（最多 5 个）
        :return:
        """
        return await self.send_rpc_json('getBundleStatuses', [param])

    @catch_exceptions(option='获取小费账户')
    async def get_tip_accounts(self) -> List[str]:
        """
            api文档参考：https://jito-labs.gitbook.io/mev/searcher-resources/json-rpc-api-reference/bundles/gettipaccounts
        :return:
        """
        return await self.send_rpc_json('getTipAccounts', [])

    # @catch_exceptions(option='模拟捆绑交易')
    # async def simulate_bundle(self, bundles: List[TX], simulation_config=None) -> Dict:
    #     for bundle in bundles:
    #         assert len(bytes(bundle)) < 1232, f'数据太大{len(bytes(bundle))}'
    #     simulation_config = simulation_config or {'transactionEncoding': 'base64'}
    #     encodedTransactions = [base64.b64encode(bytes(bundle)).decode() for bundle in bundles]
    #     params = [{'encodedTransactions': encodedTransactions}, simulation_config]
    #     headers = {'Content-Type': 'application/json'}
    #     data = {
    #         'jsonrpc': '2.0',
    #         'id': 1,
    #         'method': 'simulateBundle',
    #         'params': params,
    #     }
    #     data = await self.make_request('https://mainnet.block-engine.jito.wtf', method='POST', json=data, headers=headers,
    #                                    proxy=os.getenv('PROXY'))
    #     try:
    #         return data['result']
    #     except KeyError:
    #         raise Exception(data['error'])

    @catch_exceptions(option='发送捆绑交易')
    async def send_bundle(self, bundles: List[TX]) -> str:
        """
            api文档参考：https://jito-labs.gitbook.io/mev/searcher-resources/json-rpc-api-reference/bundles/sendbundle
        :param bundles: REQUIRED 完全签名的交易，以 base-58 编码的字符串形式（最多 5 个）。目前不支持 base-64 编码的交易。
        :return:
        """
        for bundle in bundles:
            assert len(bytes(bundle)) < 1232, f'数据太大{len(bytes(bundle))}'
        param = [based58.b58encode(bytes(bundle)).decode() for bundle in bundles]
        return await self.send_rpc_json('sendBundle', [param])

    async def wait_down(self, bundle_id: str):
        while True:
            result = await self.get_inflight_bundle_statuses([bundle_id])
            if result['value'][0]['status'] == 'Failed':
                logger.error(f'打包失败')
                break
            if result['value'][0]['status'] == 'Landed':
                logger.error(f'打包成功=>{bundle_id}')
                break

    @catch_exceptions(option='发送交易')
    async def send_transaction(self, tx: str):
        """
            api文档参考：https://jito-labs.gitbook.io/mev/searcher-resources/json-rpc-api-reference/transactions-endpoint/sendtransaction
        :param tx: REQUIRED第一个交易签名嵌入在交易中，以 base-58 编码的字符串形式
        :return:
        """
        return await self.send_rpc_json('sendTransaction', [tx])

    # @classmethod
    # async def test(cls):
    #     from logger import log_setup
    #     import logging
    #     from solana.rpc.async_api import AsyncClient
    #     from wallet import Wallet
    #     log_setup('JitoBundleTest', level=logging.DEBUG, log_path=None)
    #     wallet01 = Wallet.load(f'../wallet-data/dev-wallet-01.json')
    #     wallet02 = Wallet.load(f'../wallet-data/dev-wallet-02.json')
    #     client = AsyncClient("https://api.testnet.solana.com")
    #
    #     instance = JitoBundleClient()
    #     await instance.initialize()
    #     try:
    #         tip_accounts = await instance.get_tip_accounts()
    #         tip_account = Pubkey.from_string('B1mrQSpdeMU9gCvkJ6VsXVVoYjRGkNA7TtjMyqxrhecH')
    #         block_hash_resp = await client.get_latest_blockhash()
    #         block_hash = block_hash_resp.value.blockhash
    #         tx1 = wallet01.transfer(wallet02.public_key, 100_000_000, block_hash)
    #         tx2 = wallet01.transfer(wallet02.public_key, 50_000_000, block_hash)
    #         tx3 = wallet01.transfer(tip_account, 10_000, block_hash)
    #         bundle_id = await instance.send_bundle([tx1, tx2, tx3])
    #         while True:
    #             result = await instance.get_inflight_bundle_statuses([bundle_id])
    #             if result['value'][0]['status'] == 'Failed':
    #                 logger.error(f'打包失败')
    #                 break
    #
    #     finally:
    #         await instance.close()


jito_client = JitoClient()
