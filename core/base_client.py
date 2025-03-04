# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/15 15:14
@Author     : lkkings
@FileName:  : base_client.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
import time
from abc import ABC
from typing import Dict, Union, Any, List

import aiohttp

from core.constants import *
from logger import catch_exceptions


class Client(ABC):

    def __init__(self):
        self._url = None
        self._session: aiohttp.ClientSession | None = None
        self._background_tasks = []

    @catch_exceptions(option='客户端发送请求')
    async def make_request(self, url: str, method='GET', **kwargs) -> Union[Dict[str, Any], List, str]:
        async with self._session.request(url=url, method=method, **kwargs) as r:
            r.raise_for_status()
            return await r.json()

    async def initialize(self):
        self._session = aiohttp.ClientSession()

    async def ping(self, url: str) -> int:
        delay = 0
        for i in range(10):
            start_time = time.time()
            await self._session.get(url)
            delay += time.time() - start_time
        return int(delay * 100)

    async def close(self):
        if self._session is not None:
            await self._session.close()
            self._session = None
        for pending_task in self._background_tasks:
            try:
                pending_task.cancel()
            except asyncio.CancelledError:
                pass
