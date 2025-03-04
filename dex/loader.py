# -*- coding: utf-8 -*-
"""
@Description:
@Date       : 2024/8/24 1:47
@Author     : lkkings
@FileName:  : loader.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
from typing import List, Dict, Set, Tuple
import os.path as osp

from solders.instruction import AccountMeta
from solders.pubkey import Pubkey
from anchorpy import Idl, Program, Context, Provider
from spl.token.constants import TOKEN_PROGRAM_ID

from clients.rpc import connection
from core.base_amm import Amm
from core.base_dex import Dex
from core.constants import SwapMode, BASE_MINT, DATA_PATH, JUPITER
from core.types.dex import Market, Route, AccountInfo, QuoteParams, SwapRoute, TradeOutputOverride, SwapParams, \
    SwapLegType
from dex.market_graph import market_graph
from logger import logger
from wallet import Wallet


class DexLander:

    def __init__(self):
        self.base_mint = str(BASE_MINT)
        self.dexs: List[Dex] = []
        self.route_cache: Dict[str, List[Route]] = {}

        self._wallet: Wallet | None = None
        self._update_account_amms_ref: Dict[str, Set[Amm]] = {}

    def bind_wallet(self, wallet: Wallet):
        self._wallet = wallet

    @property
    def wallet(self):
        return self._wallet

    async def initialize(self):
        assert self.dexs, '未发现DEX交易所'
        assert self._wallet, f'请先绑定交易钱包'
        await asyncio.wait([dex.initialize() for dex in self.dexs])
        await self._wallet.initialize()

    def get_all_amm_by_update_account(self, update_accounts: List[str]) -> List[Amm]:
        if len(self._update_account_amms_ref) == 0:
            for amm in self.get_all_pools():
                for update_account in amm.accounts_for_update:
                    if update_account not in self._update_account_amms_ref:
                        self._update_account_amms_ref[update_account] = {amm}
                    else:
                        self._update_account_amms_ref[update_account].add(amm)
        amms = []
        for update_account in update_accounts:
            if update_account in self._update_account_amms_ref:
                amms.extend(self._update_account_amms_ref.get(update_account))
        return amms

    def get_markets_for_pair(self, mint1: str, mint2: str) -> List[Market]:
        markets = []
        for dex in self.dexs:
            markets.extend(dex.get_markets_for_pair(mint1, mint2))
        return markets

    def get_all_2_hop_routes(self, source_mint: str, destination_mint: str) -> List[Route]:
        cache_key = f"{source_mint}-{destination_mint}"
        cache_key_reverse = f"{destination_mint}-{source_mint}"

        if cache_key in self.route_cache:
            logger.debug(f"命中路由缓存 {cache_key}")
            return self.route_cache[cache_key]

        source_neighbours = market_graph.get_neighbours(source_mint)
        dest_neighbours = market_graph.get_neighbours(destination_mint)
        if len(source_neighbours) < len(dest_neighbours):
            intersections = source_neighbours.intersection(dest_neighbours)
        else:
            intersections = dest_neighbours.intersection(source_neighbours)

        routes = []
        routes_reverse = []

        for intersection in intersections:
            hop1 = market_graph.get_markets(source_mint, intersection)
            hop2 = market_graph.get_markets(intersection, destination_mint)

            for hop1_market in hop1:
                for hop2_market in hop2:
                    routes.append(Route(hop1_market, hop2_market))
                    routes_reverse.append(Route(hop2_market, hop1_market))

        self.route_cache[cache_key] = routes
        self.route_cache[cache_key_reverse] = routes_reverse
        return routes

    def get_most_height_value_route(self, source_mint: str, destination_mint: str, amount: int) -> List[SwapRoute]:
        """
        获取A到B最有价值的路由
        :param amount:
        :param source_mint:
        :param destination_mint:
        :return:
        """
        best_height_estimated_out = 0
        markets = self.get_markets_for_pair(source_mint, destination_mint)
        swap_routes = None
        for market in markets:
            out_amount = self.get_out_amount_market(
                market, source_mint, amount
            )
            if out_amount > best_height_estimated_out:
                swap_routes = [
                    SwapRoute(
                        market=market,
                        fromA=source_mint == market.tokenMintA,
                        trade_output_override=TradeOutputOverride(
                            in_=amount,
                            estimated_out=out_amount
                        )
                    )
                ]
                best_height_estimated_out = out_amount
        routes = self.get_all_2_hop_routes(source_mint, destination_mint)
        for route in routes:
            intermediate_out_amount = self.get_out_amount_market(
                route.hop1, source_mint, amount
            )
            is_source_mint = route.hop1.tokenMintA == source_mint
            intermediate_mint = route.hop1.tokenMintB if is_source_mint else route.hop1.tokenMintA
            out_amount = self.get_out_amount_market(
                route.hop2, intermediate_mint, intermediate_out_amount
            )
            if out_amount > best_height_estimated_out:
                swap_routes = [
                    SwapRoute(
                        market=route.hop1,
                        fromA=is_source_mint,
                        trade_output_override=TradeOutputOverride(
                            in_=amount,
                            estimated_out=intermediate_out_amount
                        )
                    ),
                    SwapRoute(
                        market=route.hop2,
                        fromA=intermediate_mint == route.hop2.tokenMintA,
                        trade_output_override=TradeOutputOverride(
                            in_=intermediate_out_amount,
                            estimated_out=out_amount
                        )
                    )
                ]
                best_height_estimated_out = out_amount
            assert swap_routes, f'未发现{source_mint}=>{destination_mint}的交易路线'
            return swap_routes

    def get_most_low_value_route(self, source_mint: str, destination_mint: str, amount: int) -> List[SwapRoute]:
        best_low_estimated_out, swap_routes = float("inf"), None
        markets = self.get_markets_for_pair(source_mint, destination_mint)
        for market in markets:
            out_amount = self.get_out_amount_market(
                market, source_mint, amount
            )
            if out_amount < best_low_estimated_out:
                swap_routes = [
                    SwapRoute(
                        market=market,
                        fromA=source_mint == market.tokenMintA,
                        trade_output_override=TradeOutputOverride(
                            in_=amount,
                            estimated_out=out_amount
                        )
                    )
                ]
                best_low_estimated_out = out_amount
        routes = self.get_all_2_hop_routes(source_mint, destination_mint)
        for route in routes:
            out_amount1 = self.get_out_amount_market(
                route.hop1, source_mint, amount
            )
            is_source_mint = route.hop1.tokenMintA == source_mint
            intermediate_mint = route.hop1.tokenMintB if is_source_mint else route.hop1.tokenMintA
            out_amount2 = self.get_out_amount_market(
                route.hop2, intermediate_mint, out_amount1
            )
            if out_amount2 < best_low_estimated_out:
                swap_routes = [
                    SwapRoute(
                        market=route.hop1,
                        fromA=is_source_mint,
                        trade_output_override=TradeOutputOverride(
                            in_=amount,
                            estimated_out=out_amount1
                        )
                    ),
                    SwapRoute(
                        market=route.hop2,
                        fromA=intermediate_mint == route.hop2.tokenMintA,
                        trade_output_override=TradeOutputOverride(
                            in_=out_amount1,
                            estimated_out=out_amount2
                        )
                    )
                ]
                best_low_estimated_out = out_amount2
            assert swap_routes, f'未发现{source_mint}=>{destination_mint}的交易对'
            return swap_routes

    def get_out_amount_route(self, route: Route, source_mint: str, amount: int):
        amount = self.get_pool(route.hop1.id).get_quote(QuoteParams(
            source_mint=Pubkey.from_string(source_mint),
            amount=amount,
            swap_mode=SwapMode.ExactIn
        )).out_amount
        is_source_mint = route.hop1.tokenMintA == source_mint
        intermediate_mint = route.hop1.tokenMintB if is_source_mint else route.hop1.tokenMintA
        amount = self.get_pool(route.hop2.id).get_quote(QuoteParams(
            source_mint=Pubkey.from_string(intermediate_mint),
            amount=amount,
            swap_mode=SwapMode.ExactIn
        )).out_amount
        return amount

    def get_out_amount_market(self, market: Market, source_mint: str, amount: int) -> int:
        return self.get_pool(market.id).get_quote(QuoteParams(
            source_mint=Pubkey.from_string(source_mint),
            amount=amount,
            swap_mode=SwapMode.ExactIn
        )).out_amount

    def get_value_mint_amount(self, mint: str, amount: int, is_negative=True) -> int:
        if mint == self.base_mint or mint == 0:
            return amount
        values = []
        markets = self.get_markets_for_pair(mint, self.base_mint)
        for market in markets:
            try:
                values.append(self.get_out_amount_market(market, mint, amount))
            except Exception as e:
                logger.warning(e)
        routes = self.get_all_2_hop_routes(mint, self.base_mint)
        for route in routes:
            try:
                values.append(self.get_out_amount_route(route, mint, amount))
            except Exception as e:
                logger.warning(e)
        if len(values) == 0:
            return 0
        else:
            return min(values) if is_negative else max(values)

    def get_pool(self, pool_id: str) -> Amm:
        for dex in self.dexs:
            if dex.pools.get(pool_id):
                return dex.pools.get(pool_id)

    def get_all_pools(self) -> List[Amm]:
        pools: List[Amm] = []
        for dex in self.dexs:
            pools.extend(dex.pools.values())
        return pools

    def get_market(self, pool_id: str) -> Market:
        for dex in self.dexs:
            if pool_id in dex.markets:
                return dex.markets.get(pool_id)

    def get_all_markets(self) -> List[Market]:
        markets: List[Market] = []
        for dex in self.dexs:
            markets.extend(dex.get_all_markets())
        return markets

    def get_swap_leg_and_accounts(self, swap_routes: List[SwapRoute]) -> Tuple[SwapLegType, List[AccountMeta]]:
        swap_legs, remaining_accounts = [], []
        for swap_route in swap_routes:
            source_mint = swap_route.market.tokenMintA if swap_route.fromA else swap_route.market.tokenMintB
            source_mint = Pubkey.from_string(source_mint)
            destination_mint = swap_route.market.tokenMintB if swap_route.fromA else swap_route.market.tokenMintA
            destination_mint = Pubkey.from_string(destination_mint)
            user_source_token_account = self._wallet.get_associated_token_account(source_mint)
            assert user_source_token_account, f'请先创建{source_mint}的关联账号'
            user_destination_token_account = self._wallet.get_associated_token_account(destination_mint)
            assert user_destination_token_account, f'请先创建{destination_mint}的关联账号'
            leg, accounts = self.get_pool(swap_route.market.id).get_swap_leg_and_accounts(
                SwapParams(
                    source_mint=source_mint,
                    destination_mint=destination_mint,
                    user_source_token_account=user_source_token_account,
                    user_destination_token_account=user_destination_token_account,
                    user_transfer_authority=self._wallet.public_key,
                    amount=swap_route.trade_output_override.in_,
                    swap_mode=SwapMode.ExactIn,
                    open_orders_address=None,
                    quote_mint_to_referrer=None
                )
            )
            swap_legs.append(leg)
            remaining_accounts.extend(accounts)
        return {'Chain': {'swap_legs': swap_legs}}, remaining_accounts

    async def close(self):
        pass


dex_loader = DexLander()
