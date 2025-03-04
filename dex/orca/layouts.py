# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/24 22:55
@Author     : lkkings
@FileName:  : layouts.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from construct import Int8ul, Int64ul
from construct import Struct as CStruct

from construct import Bytes

PUBKEY_LAYOUT = Bytes(32)

TOKEN_SWAP_LAYOUT = CStruct(
    'version' / Int8ul,
    'isInitialized' / Int8ul,
    'bumpSeed' / Int8ul,
    'poolTokenProgramId' / PUBKEY_LAYOUT,
    'tokenAccountA' / PUBKEY_LAYOUT,
    'tokenAccountB' / PUBKEY_LAYOUT,
    'tokenPool' / PUBKEY_LAYOUT,
    'mintA' / PUBKEY_LAYOUT,
    'mintB' / PUBKEY_LAYOUT,
    'feeAccount' / PUBKEY_LAYOUT,
    'tradeFeeNumerator' / Int64ul,
    'tradeFeeDenominator' / Int64ul,
    'ownerTradeFeeNumerator' / Int64ul,
    'ownerTradeFeeDenominator' / Int64ul,
    'ownerWithdrawFeeNumerator' / Int64ul,
    'ownerWithdrawFeeDenominator' / Int64ul,
    'hostFeeNumerator' / Int64ul,
    'hostFeeDenominator' / Int64ul,
    'curveType' / Int8ul,
    'curveParameters' / Bytes(32)
)

SWAP_INFO_LAYOUT = CStruct(
    'version' / Int8ul,
    'isInitialized' / Int8ul,
    'nonce' / Int8ul,
    'amplificationCoefficient' / Int64ul,
    'feeNumerator' / Int64ul,
    'adminFeeNumerator' / Int64ul,
    'tokenAccountsLength' / Int8ul,
    'precisionFactor' / Int64ul,
    'precisionMultiplierA' / Int64ul,
    'precisionMultiplierB' / Int64ul,
    'precisionMultiplierC' / Int64ul,
    'precisionMultiplierD' / Int64ul,
    'tokenAccountA' / PUBKEY_LAYOUT,
    'tokenAccountB' / PUBKEY_LAYOUT,
    'tokenAccountC' / PUBKEY_LAYOUT,
    'tokenAccountD' / PUBKEY_LAYOUT
)