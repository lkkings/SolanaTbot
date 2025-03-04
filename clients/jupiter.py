# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/25 20:40
@Author     : lkkings
@FileName:  : jupiter.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
import base64
from typing import Dict, Any, Tuple, List
from urllib.parse import urljoin

from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from spl.token.constants import WRAPPED_SOL_MINT

from core.base_client import Client
from core.constants import JUPITER, BASE_MINT

from logger import catch_exceptions, logger


def deserialize_instruction(instruction: Dict) -> Instruction:
    return Instruction(
        program_id=Pubkey.from_string(instruction['programId']),
        accounts=[AccountMeta(
            pubkey=Pubkey.from_string(i['pubkey']),
            is_signer=i['isSigner'],
            is_writable=i['isWritable']
        ) for i in instruction['accounts']],
        data=base64.b64decode(instruction['data']),
    )


class JupiterClient(Client):

    def __init__(self):
        super().__init__()
        self._base_rate = 0

    def sol_2_base_mint(self, amount: int) -> int:
        return int(self._base_rate * amount)

    def base_mint_2_sol(self, amount: int) -> int:
        return int(amount // self._base_rate)

    async def initialize(self):
        await super().initialize()
        self._base_rate = await self.vs_token(str(WRAPPED_SOL_MINT), str(BASE_MINT))
        flush_sol_value_task = asyncio.create_task(self._flush_sol_value_task())
        self._background_tasks.append(flush_sol_value_task)

    async def _flush_sol_value_task(self):
        while True:
            try:
                self._base_rate = await self.vs_token(str(WRAPPED_SOL_MINT), str(BASE_MINT))
            except Exception as e:
                logger.error(e)
            finally:
                await asyncio.sleep(3)

    async def vs_token(self, base_mint: str, target_mint: str) -> int:
        if base_mint == target_mint:
            self._base_rate = 1
        endpoint_url = urljoin(JUPITER.PRICE_HOST, '/v6/price')
        params = {
            'ids': base_mint,
            'vsToken': target_mint
        }
        resp = await self.make_request(url=endpoint_url, method='GET', params=params)
        assert resp['data'].get(base_mint), '获取价格失败'
        return int(resp['data'].get(base_mint)['price'])

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
        endpoint_url = urljoin(JUPITER.SWAP_HOST, '/v6/quote')
        params = {
            'inputMint': input_mint,
            'outputMint': output_mint,
            'amount': amount,
            'slippageBps': slippage_bps * 100
        }
        return await self.make_request(url=endpoint_url, method='GET', params=params)

    async def _get_swap(self, quote_response: Dict,
                        payer: str, wrap_and_unwrap_sol, slippage_bps: int, i: int) -> Tuple[int, Dict[str, Any]]:
        endpoint_url = urljoin(JUPITER.SWAP_HOST, '/v6/swap-instructions')
        json_data = {
            'quoteResponse': quote_response,
            'userPublicKey': payer,
            'wrapAndUnwrapSol': wrap_and_unwrap_sol,
            'dynamicSlippage': {'maxBps': slippage_bps},
        }
        return i, await self.make_request(url=endpoint_url, method='POST', json=json_data)

    @catch_exceptions(option='交换Token')
    async def multiple_swap(self, quote_responses: List[Dict],
                            payer: Pubkey, wrap_and_unwrap_sol=True,
                            slippage_bps=300) -> Tuple[List[List[Instruction]], List[Pubkey]]:
        swap_tasks, i = [], 0
        for quote_response in quote_responses:
            swap_tasks.append(asyncio.create_task(
                self._get_swap(quote_response, str(payer), wrap_and_unwrap_sol, slippage_bps, i)
            ))
            i += 1
        all_swap_transactions = [[]] * len(swap_tasks)
        down, _ = await asyncio.wait(swap_tasks)
        all_address_lookup_table_addresses = []
        for task in down:
            i, swap_transaction_resp = task.result()
            swap_transaction = []
            setupInstructions = [deserialize_instruction(i) for i in swap_transaction_resp['setupInstructions']]
            swap_transaction.extend(setupInstructions)
            swap_transaction.append(deserialize_instruction(swap_transaction_resp['swapInstruction']))
            if swap_transaction_resp.get('cleanupInstruction'):
                swap_transaction.append(deserialize_instruction(swap_transaction_resp['cleanupInstruction']))
            address_lookup_table_addresses = swap_transaction_resp['addressLookupTableAddresses']
            address_lookup_table_addresses = [Pubkey.from_string(i) for i in address_lookup_table_addresses]
            all_address_lookup_table_addresses.extend(address_lookup_table_addresses)
            all_swap_transactions[i] = swap_transaction
        return all_swap_transactions, all_address_lookup_table_addresses

    async def swap(self, quote_response: Dict, payer: Pubkey) -> Tuple[List[List[Instruction]], List[Pubkey]]:
        return await self.multiple_swap([quote_response], payer)

    @catch_exceptions(option='创建限价单')
    async def create_order(self, input_mint: str, output_mint: str, in_amount: int, out_amount: int, owner: str,
                           expired_at=None) -> Tuple[Keypair, VersionedTransaction]:
        endpoint_url = urljoin(JUPITER.ORDER_HOST, '/api/limit/v1/createOrder')
        base = Keypair()
        json_data = {
            'owner': owner,
            'inputMint': input_mint,
            'outputMint': output_mint,
            'inAmount': in_amount,
            'outAmount': out_amount,
            'expired_at': expired_at,
            'base': str(base.pubkey())
        }
        tx_base64_str = await self.make_request(url=endpoint_url, method='POST', json=json_data)
        tx = VersionedTransaction.from_bytes(base64.b64decode(tx_base64_str))
        return base, tx


jupiter_client = JupiterClient()

if __name__ == '__main__':
    from wallet import Wallet


    async def main():
        wallet = Wallet.local()
        await jupiter_client.initialize()
        a = await jupiter_client.quote(
            'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
            'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
            1000,
            300
        )
        logger.info(a)


    asyncio.run(main())
