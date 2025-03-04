# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/3 22:37
@Author     : lkkings
@FileName:  : constants.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from solders.pubkey import Pubkey

from enum import Enum
from _token import Token

import os
from dotenv import load_dotenv

# 加载 .env.example 文件
load_dotenv()


class NETWORK_TYPE(Enum):
    MAIN = 'mainnet'
    DEV = 'devnet'
    TEST = 'testnet'


class DexLabel(Enum):
    ORCA = 'Orca'
    ORCA_WHIRLPOOLS = 'Orca (Whirlpools)'
    RAYDIUM = 'Raydium'
    RAYDIUM_CLMM = 'Raydium CLMM'


class AmmLabel(Enum):
    ORCA = 'Orca'
    ORCA_WHIRLPOOLS = 'Orca (Whirlpools)'
    RAYDIUM = 'Raydium'
    RAYDIUM_CLMM = 'Raydium CLMM'


class SwapMode(Enum):
    ExactIn = "ExactIn"
    ExactOut = "ExactOut"


class TOKEN:
    USTC = Token('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', 6, 'USTC')
    SOL = Token('So11111111111111111111111111111111111111112', 9, 'SOL')


class JITO_MAIN:
    TIP_PERCENT = int(os.getenv('JTTO_TIP_PERCENT', 50))
    MIN_TIP_LAMPORTS = int(os.getenv('JITO_MIN_TIP_LAMPORTS', 10000))
    FEES_LAMPORTS = int(os.getenv('JITO_FEES_LAMPORTS', 15000))


class HELIUS_MAIN:
    HOST = 'https://api.helius.xyz/v0/webhooks'
    API_KEY = os.getenv('HELIUS_API_KEY')
    WEBHOOK = os.getenv('HELIUS_WEBHOOK')
    COVER_WEBHOOK = int(os.getenv('HELIUS_COVER_WEBHOOK'))
    WEBHOOK_TYPE = os.getenv('HELIUS_WEBHOOK_TYPE')
    assert WEBHOOK_TYPE in ['raw', 'enhanced']
    AUTH_HEADER = os.getenv('HELIUS_AUTH_HEADER')


class SOLEND_MAIN:
    PROGRAM_ID = Pubkey.from_string('So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo')

    LIQUIDITY = Pubkey.from_string(os.getenv('SOLEND_LIQUIDITY'))

    RESERVE = Pubkey.from_string(os.getenv('SOLEND_RESERVE'))

    POOL = Pubkey.from_string(os.getenv('SOLEND_POOL'))

    FEE_RECEIVER = Pubkey.from_string(os.getenv('SOLEND_FEE_RECEIVER'))

    FLASHLOAN_FEE_BPS = int(os.getenv('SOLEND_FLASHLOAN_FEE_BPS'))


class SOLEND_DEV:
    PROGRAM_ID = Pubkey.from_string('ALend7Ketfx5bxh6ghsCDXAoDrhvEmsXT3cynB6aPLgx')


class RAYDIUM_MAIN:
    OPEN_BOOK_PROGRAM = Pubkey.from_string('srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX')
    AMM_PROGRAM_ID = Pubkey.from_string('675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8')
    AUTHORITY = Pubkey.from_string("5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1")


class RAYDIUM_DEV:
    OPEN_BOOK_PROGRAM = Pubkey.default()
    AMM_PROGRAM_ID = Pubkey.from_string('HWy1jotHpo6UqeQxx49dpYYdQB8wj9Qk9MdxwjLvDHB8')
    AUTHORITY = Pubkey.default()


class JUPITER_MAIN:
    SWAP_HOST = 'https://quote-api.jup.ag'
    ORDER_HOST = 'https://jup.ag'
    PRICE_HOST = 'https://price.jup.ag'


# class JUPITER_MAIN:
#     PROGRAM_ID = Pubkey.from_string('JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB')
#
#
# class JUPITER_DEV:
#     PROGRAM_ID = Pubkey.from_string('BHzPYvC5J38kUeqkcUXwfraLWJ68cmGWm43ksF3i8bmk')


class RPC:
    HOST = os.getenv('RPC_HOST')
    DEFAULT_REQUESTS_PER_SECOND = int(os.getenv('RPC_DEFAULT_REQUESTS_PER_SECOND'))
    DEFAULT_MAX_BATCH_SIZE = int(os.getenv('RPC_DEFAULT_MAX_BATCH_SIZE'))


BASE_MINT = Pubkey.from_string(os.getenv('BASE_MINT'))
TARGET_MINT = Pubkey.from_string(os.getenv('TARGET_MINT'))
MAX_SEED_LENGTH = 32
DATA_PATH = os.getenv('DATA_PATH')
os.makedirs(DATA_PATH, exist_ok=True)
MAX_THREAD_NUM = int(os.getenv('MAX_THREAD_NUM'))

NETWORK = NETWORK_TYPE.MAIN

if NETWORK == NETWORK_TYPE.MAIN:
    JUPITER = JUPITER_MAIN
    RAYDIUM = RAYDIUM_MAIN
    HELIUS = HELIUS_MAIN
    SOLEND = SOLEND_MAIN
    JITO = JITO_MAIN
else:
    raise Exception(f'暂时不支持网络{NETWORK.name}')
