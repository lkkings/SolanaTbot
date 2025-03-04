# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/7 21:41
@Author     : lkkings
@FileName:  : base_amm.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from abc import ABC, abstractmethod
from typing import List

from solders.instruction import Instruction
from solders.pubkey import Pubkey

from core.constants import AmmLabel
from core.types.dex import ExactOutSwapParams, SwapParams, SwapLegAndAccounts, Quote, QuoteParams, AccountInfoMap


class Amm(ABC):
    label: AmmLabel
    id: str
    reserve_token_mints: List[Pubkey]
    has_dynamic_accounts: bool
    should_prefetch: bool
    exact_output_supported: bool
    fee_rate_bps: int

    def __init__(self):
        self.is_initialized = False

    @property
    def accounts_for_update(self) -> List[str]:
        return list(set(str(account) for account in self.get_accounts_for_update()))

    @abstractmethod
    def get_accounts_for_update(self) -> List[Pubkey]:
        raise NotImplementedError

    @abstractmethod
    def update(self, account_info_map: AccountInfoMap) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_quote(self, quote_params: QuoteParams) -> Quote:
        raise NotImplementedError

    @abstractmethod
    def get_swap_leg_and_accounts(self, swap_params: SwapParams) -> SwapLegAndAccounts:
        raise NotImplementedError

    @abstractmethod
    def create_exact_out_swap_instruction(self, swap_params: ExactOutSwapParams) -> Instruction:
        raise NotImplementedError

    def __repr__(self):
        return f'{self.__class__.__name__}({self.label.value},{self.id})'
