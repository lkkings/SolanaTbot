import asyncio
import json
import logging
import threading
import time
from typing import Optional, Dict, Type, Tuple, List, overload
from queue import Queue
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment, Processed
from solana.rpc.providers.async_http import AsyncHTTPProvider
from solana.rpc.providers.core import DEFAULT_TIMEOUT, T
from solders.hash import Hash
from solders.pubkey import Pubkey
from solders.rpc.responses import batch_from_json as batch_resp_json
from solders.rpc.requests import Body
from solders.rpc.responses import RPCResult

from core.constants import RPC
from core.types.dex import AccountInfoMap
from logger import logger, catch_exceptions


class TokenBucket:
    def __init__(self, capacity, interval_ms):
        self.capacity = capacity
        self.interval_ms = interval_ms
        self.tokens = capacity
        self.last_refill = asyncio.get_event_loop().time()
        self._lock = asyncio.Lock()
        # 定期填充令牌
        self._start_refill()

    def _start_refill(self):
        loop = asyncio.get_event_loop()
        loop.call_later(self.interval_ms / 1000, self.refill)

    def refill(self):
        now = asyncio.get_event_loop().time()
        time_passed = now - self.last_refill
        intervals_passed = int(time_passed * 1000 / self.interval_ms)

        if intervals_passed > 0:
            self.tokens = min(self.capacity, self.tokens + intervals_passed)
            self.last_refill += intervals_passed * self.interval_ms / 1000
        self._start_refill()

    async def try_consume(self, tokens=1):
        async with self._lock:
            self.refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False


class CoalescingAsyncHttpProvider(AsyncHTTPProvider):

    def __init__(self, endpoint: Optional[str] = None,
                 extra_headers: Optional[Dict[str, str]] = None,
                 timeout: float = DEFAULT_TIMEOUT,
                 requests_per_second: int = RPC.DEFAULT_REQUESTS_PER_SECOND,
                 max_batch_size: int = RPC.DEFAULT_MAX_BATCH_SIZE):
        super().__init__(endpoint, extra_headers, timeout)
        self.max_batch_size = max_batch_size
        self.interval = 1 / requests_per_second
        self.bucket = TokenBucket(requests_per_second, 1000 / requests_per_second)
        self.request_queue = Queue()

    def start_requests(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._process_requests())

    @catch_exceptions(option='发送rpc请求')
    async def make_request(self, body: Body, parser: Type[T]) -> T:
        if await self.bucket.try_consume():
            return await super().make_request(body, parser)
        else:
            future = asyncio.get_event_loop().create_future()
            self.request_queue.put({
                'body': body,
                'parser': parser,
                'resolve': lambda res: future.set_result(res)
            })
            result = await future
            if isinstance(result, Exception):
                raise result
            return result

    async def make_batch_request(self, reqs: Tuple[Body, ...], parsers: Tuple[Type[T], ...]) -> Tuple[RPCResult, ...]:
        raw = await self.make_batch_request_unparsed(reqs)
        return tuple(batch_resp_json(raw, parsers))

    async def _process_requests(self):
        while True:
            if not self.request_queue.empty():
                await self._coalesce_requests()
            await asyncio.sleep(self.interval)

    async def _coalesce_requests(self):
        bodies: List[Body] = []
        parsers: List[Type[T]] = []
        resolves = []
        for _ in range(self.max_batch_size):
            if self.request_queue.empty():
                break
            request = self.request_queue.get()
            bodies.append(request['body'])
            parsers.append(request['parser'])
            resolves.append(request['resolve'])
        bodies: Tuple[Body, ...] = tuple(bodies)
        parsers: Tuple[Type[T], ...] = tuple(parsers)
        logger.info(f"合并 {len(bodies)} 个请求")
        try:
            response_data = await self.make_batch_request(bodies, parsers)
        except Exception as e:
            for resolve in resolves:
                resolve(Exception(f'网络连接失败{e}'))
        else:
            for response, resolve in zip(response_data, resolves):
                resolve(response)


class AsyncConnection(AsyncClient):

    def __init__(self, endpoint: Optional[str] = None, commitment: Optional[Commitment] = None, timeout: float = 10,
                 extra_headers: Optional[Dict[str, str]] = None) -> None:
        super().__init__(endpoint, commitment, timeout, extra_headers)
        self._provider = CoalescingAsyncHttpProvider(endpoint, extra_headers)

    async def initialize(self):

        self._provider.start_requests()

    async def get_recent_block_hash(self) -> Hash:
        recent_block_hash_resp = await self.get_latest_blockhash()
        return recent_block_hash_resp.value.blockhash
    async def get_accounts_info(self, addresses: List[str]) -> AccountInfoMap:
        if len(addresses) == 0:
            return {}
        addresses = list(set(addresses))
        accounts_info = {}

        async def _get_accounts_info(_addresses: List[str]):
            _addresses: List[Pubkey] = [Pubkey.from_string(_address) for _address in _addresses]
            while True:
                try:
                    accounts_resp = await self.get_multiple_accounts(_addresses)
                    _accounts = accounts_resp.value
                    for j in range(0, len(_accounts)):
                        accounts_info[str(_addresses[j])] = _accounts[j]
                    break
                except:
                    await asyncio.sleep(1)

        tasks = []
        for i in range(0, len(addresses), 100):
            tasks.append(
                asyncio.create_task(
                    _get_accounts_info(addresses[i:min(i + 100, len(addresses))])
                )
            )
        await asyncio.gather(*tasks)
        return accounts_info


connection = AsyncConnection(endpoint=RPC.HOST, commitment=Processed, timeout=5)
