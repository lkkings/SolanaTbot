# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/4 20:48
@Author     : lkkings
@FileName:  : types.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from typing import Union, List, NamedTuple


class ApiPoolInfoV4(NamedTuple):
    id: str
    baseMint: str
    baseMintAmount: int
    quoteMint: str
    quoteMintAmount: int
    lpMint: str
    baseDecimals: int
    quoteDecimals: int
    lpDecimals: int
    version: int
    programId: str
    authority: str
    openOrders: str
    targetOrders: str
    baseVault: str
    quoteVault: str
    withdrawQueue: str
    lpVault: str
    marketVersion: int
    marketProgramId: str
    marketId: str
    marketAuthority: str
    marketBaseVault: str
    marketQuoteVault: str
    marketBids: str
    marketAsks: str
    marketEventQueue: str
    fee_rate_bps: int
    lookupTableAccount: str = ''


class ApiPoolInfoV5(NamedTuple):
    id: str
    baseMint: str
    baseMintAmount: int
    quoteMint: str
    quoteMintAmount: int
    lpMint: str
    baseDecimals: int
    quoteDecimals: int
    lpDecimals: int
    version: int
    programId: str
    authority: str
    openOrders: str
    targetOrders: str
    baseVault: str
    quoteVault: str
    withdrawQueue: str
    lpVault: str
    marketVersion: int
    marketProgramId: str
    marketId: str
    marketAuthority: str
    marketBaseVault: str
    marketQuoteVault: str
    marketBids: str
    marketAsks: str
    marketEventQueue: str
    modelDataAccount: str
    fee_rate_bps: int
    lookupTableAccount: str = ''


ApiPoolInfoItem = Union[ApiPoolInfoV4, ApiPoolInfoV5]


class ApiPoolInfo(NamedTuple):
    official: List[ApiPoolInfoItem]
    unOfficial: List[ApiPoolInfoItem]
