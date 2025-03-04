# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/8/24 1:59
@Author     : lkkings
@FileName:  : raydium.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
import traceback
from typing import Dict, Any, List
from urllib.parse import urljoin

from solana.rpc.async_api import AsyncClient
from solders.transaction import VersionedTransaction

from dex.dex import BaseDex, decode_transaction

from logger import catch_exceptions
from wallet import Wallet


class RaydiumDex(BaseDex):
    """
    api文档参考：https://docs.raydium.io/
    """
    SWAP_HOST = 'https://transaction-v1.raydium.io'

    BASE_HOST = 'https://api-v3.raydium.io'

    VERSION = 'V0'

    @catch_exceptions(option='获取优先费用', raise_error=False)
    async def priority_fee(self):
        endpoint_url = f'{self.BASE_HOST}/main/auto-fee'
        fee_response = await self.make_request(url=endpoint_url, method='GET')
        assert fee_response.get('success') is True
        priority_fee = fee_response['data']['default']
        return priority_fee['m'], priority_fee['h'], priority_fee['vh']

    @catch_exceptions(option='获取报价')
    async def quote(self, input_mint: str, output_mint: str, amount: int, slippage_bps: float) -> Dict[str, Any]:
        """
        获取代币交换的报价。
        :param input_mint: 输入代币的 mint 地址。
        :param output_mint: 输出代币的 mint 地址。
        :param amount: 要交换的输入代币数量。
        :param slippage_bps: 允许的滑点，以基点为单位（1/100 的百分比）。
        :return: 一个字典，包含报价信息。
        """
        endpoint_url = urljoin(self.SWAP_HOST, '/compute/swap-base-in')
        # endpoint_url = f'{self.SWAP_HOST}/compute/swap-base-in'
        params = {
            'inputMint': input_mint,
            'outputMint': output_mint,
            'amount': amount,
            'slippageBps': slippage_bps * 100,
            'txVersion': self.VERSION
        }
        swap_response = await self.make_request(url=endpoint_url, method='GET', params=params)
        assert swap_response.get('success') is True, f'{swap_response["msg"]}'
        return swap_response

    @catch_exceptions(option='交换Token')
    async def swap(self, input_mint: str, output_mint: str, amount: int, slippage_bps: float) -> VersionedTransaction:
        """
        获取交易。
        :param input_mint: 输入代币的 mint 地址。
        :param output_mint: 输出代币的 mint 地址。
        :param amount: 要交换的输入代币数量。
        :param slippage_bps: 允许的滑点，以基点为单位（1/100 的百分比）。
        :return: 交易信息。
        """
        endpoint_url = urljoin(self.SWAP_HOST, '/transaction/swap-base-in')
        swap_response = await self.quote(input_mint, output_mint, amount, slippage_bps)
        is_input_sol = input_mint == self.NATIVE_MINT
        is_output_sol = output_mint == self.NATIVE_MINT
        input_account = self._token_accounts.get(input_mint) if not is_input_sol else None
        output_account = self._token_accounts.get(output_mint) if not is_output_sol else None
        json_data = {
            'wallet': str(self.wallet.public_key),
            'computeUnitPriceMicroLamports': str(self._priority_fee[self.priority]),
            'swapResponse': swap_response,
            'txVersion': self.VERSION,
            'wrapSol': is_input_sol,
            'unwrapSol': is_output_sol,
            'inputAccount': input_account,
            'outputAccount': output_account,
        }
        swap_transactions = await self.make_request(url=endpoint_url, method='POST', json=json_data)
        transactions = [decode_transaction(tx['transaction']) for tx in swap_transactions['data']]
        assert len(transactions) == 1, '交易太多'
        return transactions[0]

