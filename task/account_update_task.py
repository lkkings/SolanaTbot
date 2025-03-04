# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/15 19:23
@Author     : lkkings
@FileName:  : account_update_task.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from dataclasses import dataclass
from typing import Dict, List

from core.base_task import TaskParams, AsyncTask, TaskPayload, V
from core.types.dex import AccountInfo, AccountInfoMap
from dex.loader import dex_loader
from clients.rpc import connection
from logger import catch_exceptions, logger


@dataclass
class AccountUpdateParams(TaskParams):
    update_accounts: List[str]


@dataclass
class AccountUpdatePayload(TaskPayload):
    update_accounts_info: AccountInfoMap


class AccountUpdateTask(AsyncTask[V]):
    priority = 1000

    @catch_exceptions(option='账号更新')
    async def run(self, params: AccountUpdateParams) -> AccountUpdatePayload:
        update_accounts = []

        dexs = dex_loader.get_all_amm_by_update_account(params.update_accounts)
        for amm in dexs:
            update_accounts.extend(amm.accounts_for_update)
        update_accounts_info = await connection.get_accounts_info(update_accounts)
        for amm in dexs:
            has_null_account_info = False
            account_info_map: AccountInfoMap = {}
            for account_for_update in amm.accounts_for_update:
                account_info = update_accounts_info.get(account_for_update)
                if account_info is None:
                    has_null_account_info = True
                else:
                    account_info_map[account_for_update] = account_info
            if len(account_info_map) == len(amm.accounts_for_update):
                try:
                    amm.update(account_info_map)
                    if not has_null_account_info:
                        amm.is_initialized = True
                except Exception as e:
                    raise Exception(f'更新Pool {amm.id} 错误=>{e}')
        return AccountUpdatePayload(update_accounts_info)
