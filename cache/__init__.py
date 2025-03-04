# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/15 11:51
@Author     : lkkings
@FileName:  : __init__.py.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
import os
import os.path as osp
import pickle
from typing import Any, Callable, TypeVar, Generic

from core.constants import DATA_PATH

temp_dir = osp.join(DATA_PATH, 'cache')
os.makedirs(temp_dir, exist_ok=True)


class Cache:
    __slots__ = ['_name', '_obj']

    def __init__(self, name: str, obj: Any = None):
        self._name: str = name
        self._obj: Any = obj

    @property
    def value(self):
        return self._obj

    @property
    def name(self) -> str:
        return self._name

    @classmethod
    def read(cls, name: str) -> 'Cache':
        try:
            with open(osp.join(temp_dir, f'{name}.obj'), 'rb') as file:
                obj = pickle.load(file)
            return Cache(name, obj)
        except:
            raise Exception(f'缓存对象{name}不存在')

    @classmethod
    def try_read(cls, name: str) -> 'Cache':
        try:
            return cls.read(name)
        except:
            return cls(name)

    async def when_not_exist(self, func, *args: Any, **kwargs: Any) -> 'Cache':
        if self._obj is None or not int(os.getenv('USE_CACHE')):
            if asyncio.iscoroutinefunction(func):
                self._obj = await func(*args, **kwargs)
            else:
                self._obj = func(*args, **kwargs)
        if self._obj:
            with open(osp.join(temp_dir, f'{self._name}.obj'), 'wb') as file:
                pickle.dump(self._obj, file)
        return self
