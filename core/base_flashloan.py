# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/3 21:45
@Author     : lkkings
@FileName:  : base_flashloan.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from abc import ABC, abstractmethod

from solders.instruction import Instruction
from solders.transaction import VersionedTransaction
from solders.pubkey import Pubkey


class FlashLoan(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def create_borrow_instruction(self, amount: int, token_account: Pubkey) -> Instruction:
        pass

    @abstractmethod
    def create_repay_instruction(self, amount: int, token_account: Pubkey, user_transfer_authority: Pubkey) -> Instruction:
        pass

    @abstractmethod
    def get_fee(self, in_amount: int):
        pass
