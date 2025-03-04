# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/3 23:18
@Author     : lkkings
@FileName:  : __init__.py.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from typing import Union

from solders.pubkey import Pubkey


class Token:
    __slots__ = ['_mint', '_decimals', '_symbol']

    def __init__(self, mint: str, decimals: int, symbol: str):
        self._mint = mint
        self._decimals = decimals
        self._symbol = symbol

    def is_(self, mint: Union[str, Pubkey]) -> bool:
        if isinstance(mint, Pubkey):
            mint = str(mint)
        return self._mint == mint

    def __repr__(self):
        return f'Token({self._symbol}, {self._mint})'

    @property
    def mint(self):
        return Pubkey.from_string(self._mint)

    @property
    def decimals(self):
        return self._decimals

    @property
    def symbol(self):
        return self._symbol
