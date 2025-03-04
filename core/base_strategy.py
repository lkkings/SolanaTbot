# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/11 21:49
@Author     : lkkings
@FileName:  : base_strategy.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from typing import List, Dict, Type

from solders.transaction import VersionedTransaction

from core.types.event import Event
from clients.helius import helius_client
from core.worker import worker
from logger import logger
from task.account_update_task import AccountUpdateTask, AccountUpdatePayload, AccountUpdateParams


@dataclass
class Idea:
    amount: int
    expected_profit: int
    bundle: List[VersionedTransaction] = field(default_factory=list)


class Strategy(ABC):

    def __init__(self):
        self._webhook_id = None
        self._events: List[Type[Event]] = []
        self._addresses: List[str] = []

    async def start(self):
        await self.setup(self._events, self._addresses)
        assert len(self._events) > 0, '请设置监听事件'
        assert len(self._addresses) > 0, '清设置监听账户'
        event_types = [i.type for i in self._events]
        data = await helius_client.create_webhook(
            self._addresses, event_types
        )
        self._webhook_id = data['webhookID']
        logger.info(f'正在监听{len(data["accountAddresses"])}个账户 WebhookID:{self._webhook_id} URL:{data["webhookURL"]}')

    def _parse_event(self, data: Dict):
        for item in data:
            accounts = [i['account'] for i in item['accountData']]
            worker.run_task(
                AccountUpdateTask[AccountUpdatePayload](
                    AccountUpdateParams(
                        update_accounts=accounts
                    )
                )
            )
            for event in self._events:
                if event.is_type(item):
                    yield event.parse(item)

    @abstractmethod
    async def setup(self, event_types: List[Type[Event]], addresses: List[str]):
        pass

    async def pre_execute(self, data: Dict):
        for event in self._parse_event(data):
            if event:
                idea = await self.execute(event)
                await self.to_do(idea)

    @abstractmethod
    async def execute(self, event: Event) -> Idea:
        pass

    @abstractmethod
    async def to_do(self, idea: Idea):
        pass

    async def stop(self):
        if self._webhook_id is not None:
            await helius_client.delete_webhook(self._webhook_id)
