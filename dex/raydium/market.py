# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/8 16:21
@Author     : lkkings
@FileName:  : market.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from typing import Any, List, Dict

from solana.rpc.async_api import AsyncClient
from solders.instruction import Instruction
from solders.pubkey import Pubkey

from core.base_layout import Layout, CStruct
from core.types.dex import AccountInfo
from dex.raydium.layouts import OPEN_ORDERS_V1_LAYOUT, OPEN_ORDERS_V2_LAYOUT, MARKET_STATE_V1_LAYOUT, MARKET_STATE_V2_LAYOUT


class OpenOrders(Layout):
    def __init__(self, address: Pubkey, decoded: Dict, program_id: Pubkey):
        self.address = address
        self._program_id = program_id
        self.baseTokenTotal = None
        self.quoteTokenTotal = None
        for k, v in decoded.items():
            setattr(self, k, v)

    @classmethod
    def get_layout(cls, program_id: Pubkey) -> CStruct:
        if get_layout_version(program_id) == 1:
            return OPEN_ORDERS_V1_LAYOUT
        return OPEN_ORDERS_V2_LAYOUT

    @classmethod
    async def find_for_owner(cls, client: AsyncClient, owner_address: Pubkey, program_id: Pubkey) -> List['OpenOrders']:
        pass

    @classmethod
    async def find_for_market_and_owner(cls, client: AsyncClient, market_address: Pubkey, owner_address: Pubkey,
                                        program_id: Pubkey) -> List['OpenOrders']:
        pass

    @classmethod
    async def load(cls, client: AsyncClient, address: Pubkey, program_id: Pubkey) -> 'OpenOrders':
        pass

    @classmethod
    def from_account_info(cls, address: Pubkey, account_info: AccountInfo, program_id: Pubkey) -> 'OpenOrders':
        owner = account_info.owner
        if account_info.owner != program_id:
            raise ValueError('地址不属于程序')
        decoded = cls.get_layout(program_id).parse(account_info.data)
        if not decoded.accountFlags.initialized or not decoded.accountFlags.openOrders:
            raise Exception('未结订单账户无效')
        return OpenOrders(address, decoded, program_id)

    @classmethod
    async def make_create_account_transaction(cls, client: AsyncClient, market_address: Pubkey, owner_address: Pubkey,
                                              new_account_address: Pubkey, program_id: Pubkey) -> Instruction:
        pass

    @property
    def public_key(self):
        return self.address


PROGRAM_LAYOUT_VERSIONS = {
    '4ckmDgGdxQoPDLUkDT3vHgSAkzA3QRdNq5ywwY4sUSJn': 1,
    'BJ3jrUzddfuSrZHXSCxMUUQsjKEyLmuuyZebkcaFp2fg': 1,
    'EUqojwWA2rd19FZrzeBncJsm38Jm1hEhE3zsmX3bRc2o': 2,
    '9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin': 3,
}


def get_layout_version(program_id: Pubkey):
    return PROGRAM_LAYOUT_VERSIONS.get(str(program_id)) or 3


class Market(Layout):
    @classmethod
    def get_layout(cls, program_id: Pubkey) -> CStruct:
        if get_layout_version(program_id) == 1:
            return MARKET_STATE_V1_LAYOUT
        return MARKET_STATE_V2_LAYOUT
