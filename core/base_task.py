# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/7 20:05
@Author     : lkkings
@FileName:  : base_task.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import Any, Union, TypeVar, Generic, Optional


class TaskParams(ABC):
    pass


T = TypeVar('T', bound=TaskParams)


class TaskReq(ABC):
    params: Optional[TaskParams]

    def __init__(self, params: Optional[TaskParams], id: Optional[Union[str, int]] = None):
        self._id = id
        self.params = params

    @property
    def id(self):
        return self._id


class TaskPayload(ABC):
    pass


V = TypeVar('V', bound=TaskPayload)


class TaskResp(Generic[V]):
    error: Any
    payload: Optional[V]

    def __init__(self, id: Optional[Union[str, int]] = None,
                 payload: Optional[V] = None, error: Any = None):
        self._id = id
        self.error = error
        self.payload = payload

    @property
    def id(self):
        return self._id


class AsyncTask(Generic[V]):
    priority = 10000

    def __init__(self, message: Union[TaskReq, TaskParams]):
        super().__init__()
        self._future = None
        self._message = message

    def set_future(self, future: asyncio.Future):
        self._future = future

    async def exec(self) -> None:
        uid = uuid.uuid4()
        try:
            if isinstance(self._message, TaskReq):
                uid = self._message.id if self._message.id else uid
                resp_payload = await self.run(self._message.params)
            elif isinstance(self._message, TaskParams):
                resp_payload = await self.run(self._message)
            else:
                raise TypeError
            self._future.set_result(TaskResp(id=uid, payload=resp_payload))
        except Exception as e:
            self._future.set_result(TaskResp(id=uid, error=e))

    @abstractmethod
    async def run(self, params: TaskParams) -> TaskPayload:
        raise NotImplementedError

    def __lt__(self, other):
        return self.priority < other.priority

    def __le__(self, other):
        return self.priority <= other.priority

    def __gt__(self, other):
        return self.priority > other.priority

    def __ge__(self, other):
        return self.priority >= other.priority

    def __eq__(self, other):
        return self.priority == other.priority
