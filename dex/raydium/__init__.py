# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/2 21:14
@Author     : lkkings
@FileName:  : __init__.py.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import json
import os
import os.path as osp
import traceback
from typing import List, Dict
from solders.pubkey import Pubkey

from cache import Cache
from logger import logger
from clients.rpc import connection
from core.base_dex import Dex
from core.worker import worker
from dex.market_graph import market_graph
from dex.raydium.amm import RaydiumAmm, decode_serum_market_keys_string
from core.constants import DexLabel, DATA_PATH
from core.types.dex import Market, AccountInfo, AccountInfoMap
from dex.raydium.layouts import AMM_INFO_V4_LAYOUT, MARKET_STATE_V1_LAYOUT, MARKET_STATE_V2_LAYOUT, \
    MARKET_STATE_V3_LAYOUT, SWAP_EXACT_LAYOUT
from dex.raydium.types import ApiPoolInfo, ApiPoolInfoItem, ApiPoolInfoV4, ApiPoolInfoV5
from task.account_update_task import AccountUpdateTask, AccountUpdateParams, AccountUpdatePayload
from task.add_pool_task import AddPoolTask, AddPoolPayload, AddPoolParams

MARKETS_TO_IGNORE = [
    '9DTY3rv8xRa3CnoPoWJCMcQUSY7kUHZAoFKNsBhx8DDz',
    '2EXiumdi14E9b8Fy62QcA5Uh6WdHS2b38wtSxp72Mibj',
    '9f4FtV6ikxUZr8fAjKSGNPPnUHJEwi4jNk8d79twbyFf',
    '5NBtQe4GPZTRiwrmkwPxNdAuiVFGjQWnihVSqML6ADKT'
]

data_dir = osp.join(DATA_PATH, 'raydium')
os.makedirs(data_dir, exist_ok=True)


class RaydiumDex(Dex):
    label = DexLabel.RAYDIUM

    async def get_all_pools_info(self) -> List[ApiPoolInfoItem]:
        pools: List[ApiPoolInfoItem] = []
        pool_temp_file_path = osp.join(data_dir, f'{self.network.value}.json')
        with open(pool_temp_file_path, 'r') as f:
            data = json.load(f)
        pool_info = ApiPoolInfo(
            official=[
                ApiPoolInfoV4(**params) if params['version'] == 4 else ApiPoolInfoV5(**params)
                for params in data['official'] if params['version'] in [4, 5]
            ],
            unOfficial=[
                ApiPoolInfoV4(**params) if params['version'] == 4 else ApiPoolInfoV5(**params)
                for params in data['unOfficial'] if params['version'] in [4, 5]
            ],
        )
        logger.info(
            f'{self.label}: 找到 {len(pool_info.official)} 个官方矿池和 {len(pool_info.unOfficial)} 个非官方矿池')
        pools.extend([pool for pool in pool_info.official])
        pools.extend([pool for pool in pool_info.unOfficial])
        return pools

    async def initialize(self):
        pools: List[ApiPoolInfoItem] = await self.get_all_pools_info()
        init_addresses: List[str] = []
        for pool in pools:
            init_addresses.append(pool.id)
            init_addresses.append(pool.marketId)

        initial_accounts_cache = await Cache.try_read(
            'raydium_initial_accounts'
        ).when_not_exist(
            connection.get_accounts_info, init_addresses
        )
        initial_accounts: AccountInfoMap = initial_accounts_cache.value
        update_account_addresses = []
        for pool in pools:
            try:
                market = Market(
                    id=pool.id,
                    tokenMintA=pool.baseMint,
                    tokenVaultA=pool.baseVault,
                    tokenMintB=pool.quoteMint,
                    tokenVaultB=pool.quoteVault,
                    dexLabel=self.label.value
                )
                market_graph.add_market(market.tokenMintA, market.tokenMintB, market)
                self.add_markets_for_pair(pool.baseMint, pool.quoteMint, market)
                serum_market_id = pool.marketId
                serum_program_id = Pubkey.from_string(pool.marketProgramId)
                serum_market = Pubkey.from_string(serum_market_id)
                pool_id = Pubkey.from_string(pool.id)
                if pool.marketId not in initial_accounts:
                    logger.warning(f'未发现{serum_market}账户信息')
                    continue

                serum_params = decode_serum_market_keys_string(
                    pool_id,
                    serum_program_id,
                    serum_market,
                    initial_accounts.get(serum_market_id)
                )

                resp = await worker.run_task(
                    AddPoolTask[AddPoolPayload](
                        AddPoolParams(
                            pool_label=self.label,
                            pool_id=pool_id,
                            fee_rate_bps=pool.fee_rate_bps,
                            account_info=initial_accounts.get(pool.id),
                            serum_params=serum_params
                        )
                    )
                )
                if resp.error:
                    logger.error(resp.error)
                else:
                    amm = resp.payload.amm
                    self._pools[amm.id] = amm
                    update_account_addresses.extend(amm.accounts_for_update)
            except Exception as e:
                traceback.print_exc()
                logger.error(e)
        logger.info(f'{self.label.value} Pool 加载完成')
        await worker.run_task(
            AccountUpdateTask[AccountUpdatePayload](
                AccountUpdateParams(
                    update_accounts=update_account_addresses
                )
            )
        )
        logger.info(f'{self.label} Pool 更新账户完成')


raydium = RaydiumDex()