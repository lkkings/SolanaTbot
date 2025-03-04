# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/8 15:36
@Author     : lkkings
@FileName:  : amm.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import struct
from typing import List, Dict

from solders.pubkey import Pubkey
from solders.instruction import AccountMeta, Instruction
from spl.token.constants import TOKEN_PROGRAM_ID

from core.base_amm import Amm
from core.constants import AmmLabel, RAYDIUM, SwapMode, JUPITER
from core.math import TokenSwapConstantProduct, Fraction, ZERO_FRACTION
from core.types.dex import SerumMarketKeysString, AccountInfoMap, QuoteParams, Quote, SwapParams, \
    SwapLegAndAccounts, ExactOutSwapParams, SerumMarketKeys, AccountInfo
from dex.orca.layouts import SWAP_INFO_LAYOUT
from dex.raydium.layouts import AMM_INFO_V4_LAYOUT as AMM_INFO_LAYOUT, SWAP_EXACT_LAYOUT
from dex.raydium.market import Market as RaydiumMarket, OpenOrders
from dex.utils import generate_program_derived_address, to_array_like
from logger import catch_exceptions


def build_remaining_accounts(fee_account: Pubkey, overflow_fee_account: Pubkey):
    accounts = [AccountMeta(pubkey=overflow_fee_account, is_signer=False, is_writable=True)]
    if fee_account is not None:
        accounts.append(AccountMeta(pubkey=fee_account, is_signer=False, is_writable=True))
    return accounts


def swap_layout_decode(amm_id: Pubkey, amm_account_info: AccountInfo):
    n = amm_account_info.owner
    i = SWAP_INFO_LAYOUT.parse(amm_account_info.data)
    o = i['tokenAccountsLength']

    # 生成 authority
    s = generate_program_derived_address([bytes(amm_id), bytes([i['nonce']])], n)

    # 获取精度因子和代币账户
    a = [
            i['precisionMultiplierA'].to_number(),
            i['precisionMultiplierB'].to_number(),
            i['precisionMultiplierC'].to_number(),
            i['precisionMultiplierD'].to_number()
        ][:o]

    r = [
            i['tokenAccountA'],
            i['tokenAccountB'],
            i['tokenAccountC'],
            i['tokenAccountD']
        ][:o]

    return {
        'programId': n,
        'authority': s,
        'isInitialized': bool(i['isInitialized']),
        'nonce': i['nonce'],
        'ammId': amm_id,
        'amplificationCoefficient': i['amplificationCoefficient'].to_number(),
        'feeNumerator': i['feeNumerator'].to_number(),
        'tokenAccountsLength': o,
        'precisionFactor': i['precisionFactor'].to_number(),
        'precisionMultipliers': a,
        'tokenAccounts': r
    }


class OrcaAmm(Amm):
    label = AmmLabel.ORCA

    def __init__(self, amm_id: Pubkey, amm_account_info: AccountInfo, params):
        super().__init__()
        self.address = amm_id
        self.id = str(amm_id)
        self.should_prefetch = False
        self.exact_output_supported = False
        self.has_dynamic_accounts = False
        self.swap_layout = swap_layout_decode(amm_id, amm_account_info)
        self.calculator = self.calculator_from_swap_state(self.swap_layout)
        self.token_mints = [PublicKey(t) for t in params['tokenMints']]
        self.token_reserve_amounts = None

    def get_accounts_for_update(self) -> List[Pubkey]:
        return [self.amm_id, self.pool_coin_token_account, self.pool_pc_token_account, self.amm_open_orders]

    def update(self, account_info_map: AccountInfoMap):
        amm_account_info, pool_coin_token_account_info, pool_pc_token_account_info, amm_open_orders_account_info = [
            get_account_info(account_info_map, account) for account in self.get_accounts_for_update()
        ]
        a = struct.unpack('<Q', pool_coin_token_account_info.data[64:72])[0]
        r = struct.unpack('<Q', pool_pc_token_account_info.data[64:72])[0]
        u = OpenOrders.from_account_info(self.amm_open_orders, amm_open_orders_account_info,
                                         amm_open_orders_account_info.owner)
        c = AMM_INFO_LAYOUT.parse(amm_account_info.data)
        self.coin_reserve = a + u.baseTokenTotal - c.needTakePnlCoin
        self.pc_reserve = r + u.quoteTokenTotal - c.needTakePnlPc

    @catch_exceptions(option='获取报价')
    def get_quote(self, quote_params: QuoteParams) -> Quote:
        if not self.is_tradeable:
            raise ValueError("矿池不可交易")
        if not self.coin_reserve or not self.pc_reserve:
            raise ValueError("池代币账户余额未刷新或为空")
        quote = self.get_quote_internal(quote_params.amount, quote_params.source_mint, self.coin_reserve,
                                        self.pc_reserve,
                                        quote_params.swap_mode)
        return Quote(not_enough_liquidity=False, fee_mint=quote_params.source_mint, fee_pct=self.fee_pct.value, **quote)

    def get_swap_leg_and_accounts(self, swap_params: SwapParams) -> SwapLegAndAccounts:
        return {'Swap': {'swap': {'Raydium': {}}}}, self.build_account_keys(swap_params)

    def get_quote_internal(self, amount: int, source_mint: Pubkey,
                           coin_reserve: int, pc_reserve: int, swap_mode: SwapMode) -> Dict:
        coin_mint = 1 if self.coin_mint == source_mint else 0
        if swap_mode == SwapMode.ExactIn:
            result = self.calculator.exchange([coin_reserve, pc_reserve], amount, coin_mint)
            return {
                "in_amount": amount,
                "out_amount": result.expected_output_amount,
                "fee_amount": result.fees,
                "price_impact_pct": result.price_impact
            }
        else:
            result = self.calculator.exchange_for_exact_output([coin_reserve, pc_reserve], amount, coin_mint)
            return {
                "in_amount": result.expected_input_amount,
                "out_amount": amount,
                "fee_amount": result.fees,
                "price_impact_pct": result.price_impact
            }

    def build_account_keys(self, swap_params) -> List[AccountMeta]:
        return [
            AccountMeta(pubkey=RAYDIUM.AMM_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=self.amm_id, is_signer=False, is_writable=True),
            AccountMeta(pubkey=RAYDIUM.AUTHORITY, is_signer=False, is_writable=False),
            AccountMeta(pubkey=self.amm_open_orders, is_signer=False, is_writable=True),
            AccountMeta(pubkey=self.pool_coin_token_account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=self.pool_pc_token_account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=self.serum_program_id, is_signer=False, is_writable=False),
            AccountMeta(pubkey=self.serum_market, is_signer=False, is_writable=True),
            AccountMeta(pubkey=self.serum_market_keys.serum_bids, is_signer=False, is_writable=True),
            AccountMeta(pubkey=self.serum_market_keys.serum_asks, is_signer=False, is_writable=True),
            AccountMeta(pubkey=self.serum_market_keys.serum_event_queue, is_signer=False, is_writable=True),
            AccountMeta(pubkey=self.serum_market_keys.serum_coin_vault_account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=self.serum_market_keys.serum_pc_vault_account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=self.serum_market_keys.serum_vault_signer, is_signer=False, is_writable=False),
            AccountMeta(pubkey=swap_params.user_source_token_account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=swap_params.user_destination_token_account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=swap_params.user_transfer_authority, is_signer=True, is_writable=False)
        ]

    @property
    def reserve_token_mints(self):
        return [self.coin_mint, self.pc_mint]

    @property
    def is_tradeable(self):
        return self.status in [1, 6]
