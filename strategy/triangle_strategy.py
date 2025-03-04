# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/11 23:07
@Author     : lkkings
@FileName:  : triangle_strategy.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import time
from typing import List, Dict, Type,Union
from dataclasses import dataclass

from solders.pubkey import Pubkey

from core.base_strategy import Strategy, Idea
from core.types.event import EventType, Event
from core.worker import worker
from core.constants import BASE_MINT
from task.arb_swap_task import ArbSwapTask, ArbSwapPayload, ArbSwapParams
from dex.loader import dex_loader
from db.model import Token
from logger import logger


@dataclass
class SwapEvent(Event):
    type = EventType.SWAP
    mint1: str
    mint2: str
    amount1: int
    amount2: int
    time: int
    hash: str

    @classmethod
    def is_type(cls, data: Dict) -> bool:
        return data['type'] == cls.type.name

    @classmethod
    def parse(cls, data: Dict) -> 'Event':
        token_transfers = data['tokenTransfers']
        source_transfer = token_transfers[0]
        mint1 = source_transfer['mint']
        amount1 = source_transfer['tokenAmount']
        dest_transfer = token_transfers[-1]
        mint2 = dest_transfer['mint']
        amount2 = dest_transfer['tokenAmount']
        return cls(mint1=mint1, amount1=amount1, mint2=mint2, amount2=amount2, time=data['timestamp'],hash=data['signature'])


@dataclass
class RemoveLiquidityEvent(Event):
    type = EventType.WITHDRAW_LIQUIDITY
    mint1: str
    mint2: str
    lp_mint: str
    amount1: int
    amount2: int
    time: int
    hash: str

    @classmethod
    def is_type(cls, data: Dict) -> bool:
        return data['type'] == cls.type.name

    @classmethod
    def parse(cls, data: Dict) -> 'Event':
        token_transfers = data['tokenTransfers']
        source_transfer = token_transfers[0]
        mint1 = source_transfer['mint']
        amount1 = source_transfer['tokenAmount']
        dest_transfer = token_transfers[1]
        mint2 = dest_transfer['mint']
        amount2 = dest_transfer['tokenAmount']
        lp_mint = token_transfers[2]['mint']
        return cls(mint1=mint1, amount1=amount1, mint2=mint2, lp_mint=lp_mint, amount2=amount2, time=data['timestamp'],hash=data['signature'])


@dataclass
class AddLiquidityEvent(RemoveLiquidityEvent):
    type = EventType.ADD_LIQUIDITY


HandleEvent = Union[SwapEvent, AddLiquidityEvent, AddLiquidityEvent]


class TriangleStrategy(Strategy):
    async def to_do(self, idea: Idea):
        pass

    async def setup(self, events: List[Type[Event]], addresses: List[str]):
        events.extend([AddLiquidityEvent, RemoveLiquidityEvent, SwapEvent])
        pools = dex_loader.get_all_pools()
        update_accounts = []
        for pool in pools:
            update_accounts.extend(pool.accounts_for_update)
        addresses.extend(set(update_accounts))

    async def execute(self, event: HandleEvent) -> Idea:
        lamports1 = await Token.to_lamport(event.mint1, event.amount1)
        value1 = dex_loader.get_value_mint_amount(event.mint1, lamports1)
        symbol1 = await Token.get_symbol(mint=event.mint1)
        lamports2 = await Token.to_lamport(event.mint2, event.amount2)
        value2 = dex_loader.get_value_mint_amount(event.mint2, lamports2)
        symbol2 = await Token.get_symbol(mint=event.mint2)
        if max(value2,value1) < 10_000_000:
            return Idea(amount=int(8), expected_profit=int(8), bundle=[])

        if value1 > 1_000_000 and event.mint1 != str(BASE_MINT):
            worker.run_task(ArbSwapTask[ArbSwapPayload](
                ArbSwapParams(
                    source_mint=str(BASE_MINT),
                    destination_mint=event.mint1,
                    amount=1_000_000_000
                )
            ))
        if value2 > 1_000_000 and event.mint2 != str(BASE_MINT):
            worker.run_task(ArbSwapTask[ArbSwapPayload](
                ArbSwapParams(
                    source_mint=str(BASE_MINT),
                    destination_mint=event.mint2,
                    amount=1_000_000_000
                )
            ))
        logger.info(f'交易hash:{event.hash}')
        if event.type == EventType.WITHDRAW_LIQUIDITY:
            logger.info(
                f'[移除流动性 | {time.time() - event.time} 秒前] {symbol1}/{event.mint1} 数额:{event.amount1} 价值{value1} ')
            logger.info(
                f'[移除流动性 | {time.time() - event.time} 秒前] {symbol2}/{event.mint2} 数额:{event.amount2} 价值{value2}')
        elif event.type == EventType.ADD_LIQUIDITY:
            logger.info(
                f'[添加流动性 | {time.time() - event.time} 秒前] {symbol1}/{event.mint1} 数额:{event.amount1} 价值{value1}')
            logger.info(
                f'[添加流动性 | {time.time() - event.time} 秒前] {symbol2}/{event.mint2} 数额:{event.amount2} 价值{value2}')
        elif event.type == EventType.SWAP:
            logger.info(
                f'[添加流动性 | {time.time() - event.time} 秒前] {symbol1}/{event.mint1} 数额:{event.amount1} 价值:{value1}'
                f'=>{symbol2}/{event.mint2} 数额:{event.amount2} 价值:{value2}')

        return Idea(amount=int(8), expected_profit=int(8), bundle=[])


triangle_strategy = TriangleStrategy()
