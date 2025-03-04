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
from dex.raydium.layouts import AMM_INFO_V4_LAYOUT as AMM_INFO_LAYOUT
from dex.utils import get_account_info,generate_program_derived_address, to_array_like
from dex.raydium.market import Market as RaydiumMarket, OpenOrders
from logger import catch_exceptions


def build_remaining_accounts(fee_account: Pubkey, overflow_fee_account: Pubkey):
    accounts = [AccountMeta(pubkey=overflow_fee_account, is_signer=False, is_writable=True)]
    if fee_account is not None:
        accounts.append(AccountMeta(pubkey=fee_account, is_signer=False, is_writable=True))
    return accounts


def decode_serum_market_keys_string(raydium_amm_id: Pubkey,
                                    serum_program_id: Pubkey,
                                    serum_market: Pubkey,
                                    serum_market_info: AccountInfo) -> SerumMarketKeysString:
    if serum_program_id != RAYDIUM.OPEN_BOOK_PROGRAM:
        return SerumMarketKeys(
            serum_bids=raydium_amm_id,
            serum_asks=raydium_amm_id,
            serum_event_queue=raydium_amm_id,
            serum_coin_vault_account=raydium_amm_id,
            serum_pc_vault_account=raydium_amm_id,
            serum_vault_signer=raydium_amm_id
        )
    else:
        s = RaydiumMarket.get_layout(serum_program_id).parse(serum_market_info.data)
        a = generate_program_derived_address(
            [bytes(serum_market), to_array_like(s.get('vaultSignerNonce'), 8)], serum_program_id)
        return SerumMarketKeys(
            serum_bids=Pubkey.from_bytes(s.get('bids')),
            serum_asks=Pubkey.from_bytes(s.get('asks')),
            serum_event_queue=Pubkey.from_bytes(s.get('eventQueue')),
            serum_coin_vault_account=Pubkey.from_bytes(s.get('baseVault')),
            serum_pc_vault_account=Pubkey.from_bytes(s.get('quoteVault')),
            serum_vault_signer=a
        )


class RaydiumAmm(Amm):
    label = AmmLabel.RAYDIUM

    def __init__(self, amm_id: Pubkey, amm_account_info: AccountInfo, params: SerumMarketKeysString):
        super().__init__()
        self.amm_id = amm_id
        self.id = str(amm_id)
        self.should_prefetch = False
        self.exact_output_supported = True
        self.has_dynamic_accounts = False
        self.coin_mint = None
        self.pc_mint = None
        self.status = None
        self.serum_program_id = None
        self.serum_market = None
        self.amm_open_orders = None
        self.amm_target_orders = None
        self.pool_coin_token_account = None
        self.pool_pc_token_account = None
        self.serum_market_keys = None
        self.coin_reserve = None
        self.pc_reserve = None
        self.fee_pct = None
        self.calculator = None

        s = AMM_INFO_LAYOUT.parse(amm_account_info.data)
        self.status = s.get('status')
        self.coin_mint = Pubkey.from_bytes(s.get('coinMintAddress'))
        self.pc_mint = Pubkey.from_bytes(s.get('pcMintAddress'))
        self.pool_coin_token_account = Pubkey.from_bytes(s.get('poolCoinTokenAccount'))
        self.pool_pc_token_account = Pubkey.from_bytes(s.get('poolPcTokenAccount'))
        self.serum_program_id = Pubkey.from_bytes(s.get('serumProgramId'))
        self.serum_market = Pubkey.from_bytes(s.get('serumMarket'))
        self.amm_open_orders = Pubkey.from_bytes(s.get('ammOpenOrders'))
        self.amm_target_orders = Pubkey.from_bytes(s.get('ammTargetOrders'))

        self.serum_market_keys = params

        a = int(s.get('swapFeeNumerator'))
        r = int(s.get('swapFeeDenominator'))
        self.fee_pct = Fraction(a, r)
        self.calculator = TokenSwapConstantProduct(Fraction(a, r), ZERO_FRACTION)

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
