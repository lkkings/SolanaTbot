# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/24 22:34
@Author     : lkkings
@FileName:  : __init__.py.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import json
import os
import traceback
from typing import List
import os.path as osp

from cache import Cache
from core.base_dex import Dex
from core.constants import DexLabel, DATA_PATH
from core.types.dex import AccountInfoMap, Market
from core.worker import worker
from dex.market_graph import market_graph
from dex.orca.layouts import TOKEN_SWAP_LAYOUT
from dex.orca.types import ApiPoolInfoItem
from logger import logger
from task import AddPoolParams, AddPoolTask, AddPoolPayload

data_dir = osp.join(DATA_PATH, 'orca')
os.makedirs(data_dir, exist_ok=True)


class OrcaDex(Dex):
    label = DexLabel.ORCA

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
        pool_temp_file_path = osp.join(data_dir, f'{self.network.value}.json')
        with open(pool_temp_file_path, 'r') as f:
            data = json.load(f)
        pool_accounts = [i['poolAccount'] for i in data.values()]
        init_addresses = pool_accounts.copy()
        initial_accounts_cache = await Cache.try_read(
            'raydium_initial_accounts'
        ).when_not_exist(
            get_accounts_info, init_addresses
        )
        initial_accounts: AccountInfoMap = initial_accounts_cache.value
        update_account_addresses = []
        for pool_account in pool_accounts:
            try:
                data = initial_accounts[pool_account].data
                pool = TOKEN_SWAP_LAYOUT.parse(data)
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
                resp = await worker.run_task(
                    AddPoolTask[AddPoolPayload](
                        AddPoolParams(
                            pool_label=self.label,
                            pool_id=pool.id,
                            fee_rate_bps=pool.fee_rate_bps,
                            account_info=initial_accounts.get(pool.id)
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
