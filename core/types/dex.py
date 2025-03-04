from dataclasses import dataclass
from typing import Optional, Dict, Union, Set, List, Tuple

from solders.account import Account as AccountInfo
from solders.instruction import AccountMeta
from solders.pubkey import Pubkey

from core.constants import SwapMode
from core.types import Serial


@dataclass
class Market(Serial):
    id: str
    tokenMintA: str
    tokenVaultA: str
    tokenMintB: str
    tokenVaultB: str
    dexLabel: str


@dataclass
class TradeOutputOverride:
    in_: int
    estimated_out: int


@dataclass
class SwapRoute(Serial):
    market: Market
    fromA: bool
    trade_output_override: Optional[TradeOutputOverride]


@dataclass
class Route(Serial):
    hop1: Market
    hop2: Market


@dataclass
class Node(Serial):
    id: str
    neighbours: Set[str]


@dataclass
class SerumMarketKeys(Serial):
    serum_bids: Pubkey
    serum_asks: Pubkey
    serum_event_queue: Pubkey
    serum_coin_vault_account: Pubkey
    serum_pc_vault_account: Pubkey
    serum_vault_signer: Pubkey


SerumMarketKeysString = Union[SerumMarketKeys, str]

AccountInfoMap = Dict[str, Optional[AccountInfo]]


@dataclass
class QuoteParams(Serial):
    source_mint: Pubkey
    amount: int
    swap_mode: SwapMode = None
    destination_mint: Pubkey = None


@dataclass
class Quote(Serial):
    not_enough_liquidity: bool
    in_amount: int
    out_amount: int
    fee_amount: int
    fee_mint: Pubkey
    fee_pct: float
    price_impact_pct: float = 0
    min_in_amount: int = 0
    min_out_amount: int = 0


TokenMintAddress = Union[str]
QuoteMintToReferrer = Union[Dict[TokenMintAddress, Pubkey]]


@dataclass
class SwapParams(Serial):
    source_mint: Pubkey
    destination_mint: Pubkey
    user_source_token_account: Pubkey
    user_destination_token_account: Pubkey
    user_transfer_authority: Pubkey
    amount: int
    swap_mode: SwapMode
    open_orders_address: Optional[Pubkey]
    quote_mint_to_referrer: Optional[QuoteMintToReferrer]


@dataclass
class PlatformFee(Serial):
    fee_bps: int
    fee_account: Pubkey


@dataclass
class ExactOutSwapParams(SwapParams):
    in_amount: int
    slippage_bps: int
    platform_fee: PlatformFee
    overflow_fee_account: Pubkey


@dataclass
class SwapResult(Serial):
    price_impact: int
    fees: int
    expected_output_amount: int


@dataclass
class SwapExactOutputResult(Serial):
    price_impact: int
    fees: int
    expected_input_amount: int


SwapLegType = Dict[str, Dict]

SwapLegAndAccounts = Tuple[SwapLegType, List[AccountMeta]]


class MercurialParams(Serial):
    token_mints: List[str]
