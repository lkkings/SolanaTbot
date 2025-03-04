from typing import Union

from construct import Bytes, Int8ul, Int64ul, Padding, BitsInteger, BitsSwapped, BitStruct, Const, Flag, BytesInteger, \
    Int16ul, Array, Bit
from construct import Struct as CStruct


PUBKEY_LAYOUT = Bytes(32)

""" 
je("ammOpenOrders"), je("serumMarket"), je("serumProgramId"), je("ammTargetOrders"), je("poolWithdrawQueue"), je("poolTempLpTokenAccount"), je("ammOwner"), je("pnlOwner")]);
"""
AMM_INFO_V4_LAYOUT = CStruct(
    "status" / Int64ul,
    "nonce" / Int64ul,
    "orderNum" / Int64ul,
    "depth" / Int64ul,
    "coinDecimals" / Int64ul,
    "pcDecimals" / Int64ul,
    "state" / Int64ul,
    "resetFlag" / Int64ul,
    "minSize" / Int64ul,
    "volMaxCutRatio" / Int64ul,
    "amountWaveRatio" / Int64ul,
    "coinLotSize" / Int64ul,
    "pcLotSize" / Int64ul,
    "minPriceMultiplier" / Int64ul,
    "maxPriceMultiplier" / Int64ul,
    "systemDecimalsValue" / Int64ul,
    "minSeparateNumerator" / Int64ul,
    "minSeparateDenominator" / Int64ul,
    "tradeFeeNumerator" / Int64ul,
    "tradeFeeDenominator" / Int64ul,
    "pnlNumerator" / Int64ul,
    "pnlDenominator" / Int64ul,
    "swapFeeNumerator" / Int64ul,
    "swapFeeDenominator" / Int64ul,
    "needTakePnlCoin" / Int64ul,
    "needTakePnlPc" / Int64ul,
    "totalPnlPc" / Int64ul,
    "totalPnlCoin" / Int64ul,
    "poolTotalDepositPc" / BytesInteger(16, signed=False, swapped=True),
    "poolTotalDepositCoin" / BytesInteger(16, signed=False, swapped=True),
    "swapCoinInAmount" / BytesInteger(16, signed=False, swapped=True),
    "swapPcOutAmount" / BytesInteger(16, signed=False, swapped=True),
    "swapCoin2PcFee" / Int64ul,
    "swapPcInAmount" / BytesInteger(16, signed=False, swapped=True),
    "swapCoinOutAmount" / BytesInteger(16, signed=False, swapped=True),
    "swapPc2CoinFee" / Int64ul,
    "poolCoinTokenAccount" / PUBKEY_LAYOUT,
    "poolPcTokenAccount" / PUBKEY_LAYOUT,
    "coinMintAddress" / PUBKEY_LAYOUT,
    "pcMintAddress" / PUBKEY_LAYOUT,
    "lpMintAddress" / PUBKEY_LAYOUT,
    "ammOpenOrders" / PUBKEY_LAYOUT,
    "serumMarket" / PUBKEY_LAYOUT,
    "serumProgramId" / PUBKEY_LAYOUT,
    "ammTargetOrders" / PUBKEY_LAYOUT,
    "poolWithdrawQueue" / PUBKEY_LAYOUT,
    "poolTempLpTokenAccount" / PUBKEY_LAYOUT,
    "ammOwner" / PUBKEY_LAYOUT,
    "pnlOwner" / PUBKEY_LAYOUT,
)

ACCOUNT_FLAGS_LAYOUT = CStruct(

        "initialized" / Flag,
        "market" / Flag,
        "openOrders" / Flag,
        "requestQueue" / Flag,
        "eventQueue" / Flag,
        "bids" / Flag,
        "asks" / Flag,
"padding" / Flag,
    )

MARKET_STATE_V1_LAYOUT = CStruct(
    "Bytes_5" / Bytes(5),
    "accountFlags" / ACCOUNT_FLAGS_LAYOUT,
    "ownAddress" / PUBKEY_LAYOUT,
    "vaultSignerNonce" / Int64ul,
    "baseMint" / PUBKEY_LAYOUT,
    "quoteMint" / PUBKEY_LAYOUT,
    "baseVault" / PUBKEY_LAYOUT,
    "baseDepositsTotal" / Int64ul,
    "baseFeesAccrued" / Int64ul,
    "quoteVault" / PUBKEY_LAYOUT,
    "quoteDepositsTotal" / Int64ul,
    "quoteFeesAccrued" / Int64ul,
    "quoteDustThreshold" / Int64ul,
    "requestQueue" / PUBKEY_LAYOUT,
    "eventQueue" / PUBKEY_LAYOUT,
    "bids" / PUBKEY_LAYOUT,
    "asks" / PUBKEY_LAYOUT,
    "baseLotSize" / Int64ul,
    "quoteLotSize" / Int64ul,
    "feeRateBps" / Int64ul,
    "Bytes_7" / Bytes(7)
)

# 定义布局 V2
MARKET_STATE_V2_LAYOUT = CStruct(
    "Bytes_5" / Bytes(5),
    "accountFlags" / ACCOUNT_FLAGS_LAYOUT,
    "ownAddress" / PUBKEY_LAYOUT,
    "vaultSignerNonce" / Int64ul,
    "baseMint" / PUBKEY_LAYOUT,
    "quoteMint" / PUBKEY_LAYOUT,
    "baseVault" / PUBKEY_LAYOUT,
    "baseDepositsTotal" / Int64ul,
    "baseFeesAccrued" / Int64ul,
    "quoteVault" / PUBKEY_LAYOUT,
    "quoteDepositsTotal" / Int64ul,
    "quoteFeesAccrued" / Int64ul,
    "quoteDustThreshold" / Int64ul,
    "requestQueue" / PUBKEY_LAYOUT,
    "eventQueue" / PUBKEY_LAYOUT,
    "bids" / PUBKEY_LAYOUT,
    "asks" / PUBKEY_LAYOUT,
    "baseLotSize" / Int64ul,
    "quoteLotSize" / Int64ul,
    "feeRateBps" / Int64ul,
    "referrerRebatesAccrued" / Int64ul,
    "Bytes_7" / Bytes(7)
)

# 定义布局 V3
MARKET_STATE_V3_LAYOUT = CStruct(
    "Bytes_5" / Bytes(5),
    "accountFlags" / Int8ul,
    "ownAddress" / PUBKEY_LAYOUT,
    "vaultSignerNonce" / Int64ul,
    "baseMint" / PUBKEY_LAYOUT,
    "quoteMint" / PUBKEY_LAYOUT,
    "baseVault" / PUBKEY_LAYOUT,
    "baseDepositsTotal" / Int64ul,
    "baseFeesAccrued" / Int64ul,
    "quoteVault" / PUBKEY_LAYOUT,
    "quoteDepositsTotal" / Int64ul,
    "quoteFeesAccrued" / Int64ul,
    "quoteDustThreshold" / Int64ul,
    "requestQueue" / PUBKEY_LAYOUT,
    "eventQueue" / PUBKEY_LAYOUT,
    "bids" / PUBKEY_LAYOUT,
    "asks" / PUBKEY_LAYOUT,
    "baseLotSize" / Int64ul,
    "quoteLotSize" / Int64ul,
    "feeRateBps" / Int64ul,
    "referrerRebatesAccrued" / Int64ul,
    "authority" / PUBKEY_LAYOUT,
    "pruneAuthority" / PUBKEY_LAYOUT,
    "consumeEventsAuthority" / PUBKEY_LAYOUT,
    "Bytes_992" / Bytes(992),
    "Bytes_7" / Bytes(7)
)

AMOUNT_WITH_SLIPPAGE_LAYOUT = CStruct(
    "amount" / Int64ul,
    "slippageBps" / Int16ul
)
SWAP_EXACT_LAYOUT = CStruct(
    "outAmount" / Int64ul,
    "inAmountWithSlippage" / AMOUNT_WITH_SLIPPAGE_LAYOUT,
    "platformFeeBps" / Int8ul
)

ACCOUNT_FLAGS_LAYOUT = BitsSwapped(
    BitStruct(
        "initialized" / Flag,
        "market" / Flag,
        "openOrders" / Flag,
        "requestQueue" / Flag,
        "eventQueue" / Flag,
        "bids" / Flag,
        "asks" / Flag,
        Const(0, BitsInteger(57)),  # Padding
    )
)

OPEN_ORDERS_V1_LAYOUT = CStruct(
    "reserved" / Bytes(5),
    "accountFlags" / ACCOUNT_FLAGS_LAYOUT,
    "market" / PUBKEY_LAYOUT,
    "owner" / PUBKEY_LAYOUT,
    "baseTokenFree" / Int64ul,
    "baseTokenTotal" / Int64ul,
    "quoteTokenFree" / Int64ul,
    "quoteTokenTotal" / Int64ul,
    "freeSlotBits" / BytesInteger(16, signed=False, swapped=True),
    "isBidBits" / BytesInteger(16, signed=False, swapped=True),
    "orders" / Array(128, BytesInteger(16, signed=False, swapped=True)),
    "clientIds" / Array(128, Int64ul),
    "reserved2" / Bytes(7)
)

# Define V2 Layout
OPEN_ORDERS_V2_LAYOUT = CStruct(
    "reserved" / Bytes(5),
    "accountFlags" / ACCOUNT_FLAGS_LAYOUT,
    "market" / PUBKEY_LAYOUT,
    "owner" / PUBKEY_LAYOUT,
    "baseTokenFree" / Int64ul,
    "baseTokenTotal" / Int64ul,
    "quoteTokenFree" / Int64ul,
    "quoteTokenTotal" / Int64ul,
    "freeSlotBits" / BytesInteger(16, signed=False, swapped=True),
    "isBidBits" / BytesInteger(16, signed=False, swapped=True),
    "orders" / Array(128, BytesInteger(16, signed=False, swapped=True)),
    "clientIds" / Array(128, Int64ul),
    "referrerRebatesAccrued" / Int64ul,
    "reserved2" / Bytes(7)
)
