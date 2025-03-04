# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/8/24 1:59
@Author     : lkkings
@FileName:  : base_dex.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from abc import ABC, abstractmethod
from typing import Dict, Tuple, NamedTuple, List

from core.base_amm import Amm
from core.constants import DexLabel, NETWORK
from core.types.dex import Market, AccountInfo, AccountInfoMap


def to_pair_string(mint1: str, mint2: str) -> str:
    if mint1 < mint2:
        return f'{mint1}-{mint2}'
    else:
        return f'{mint2}-{mint1}'


class Dex(ABC):
    label: DexLabel
    network = NETWORK

    def __init__(self):
        self._pair_markets_map: Dict[str, List[Market]] = {}
        self._pools: Dict[str, Amm] = {}
        self._markets: Dict[str, Market] = {}

    @property
    def markets(self) -> Dict[str, Market]:
        return self._markets

    @property
    def pools(self) -> Dict[str, Amm]:
        return self._pools

    @property
    def pair_markets_map(self) -> Dict[str, List[Market]]:
        return self._pair_markets_map

    @abstractmethod
    async def initialize(self):
        raise NotImplementedError

    def get_markets_for_pair(self, mint1: str, mint2: str) -> List[Market]:
        markets = self._pair_markets_map.get(to_pair_string(mint1, mint2))
        return markets or []

    def add_markets_for_pair(self, mint1: str, mint2: str, market: Market):
        pair_string = to_pair_string(mint1, mint2)
        self._markets[market.id] = market
        if pair_string in self.pair_markets_map:
            self._pair_markets_map.get(pair_string).append(market)
        else:
            self._pair_markets_map[pair_string] = [market]

    def get_all_markets(self):
        all_markets = []
        for markets in self._pair_markets_map.values():
            all_markets.extend(markets)
        return all_markets
