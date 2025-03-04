# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/8/24 2:11
@Author     : lkkings
@FileName:  : http_utils.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from typing import Optional, Dict, Any

import aiohttp


class AsyncHTTPUtil:
    session: aiohttp.ClientSession | None = None

    @classmethod
    async def initialize(cls):
        if cls.session is None:
            cls.session = aiohttp.ClientSession()

    @classmethod
    async def _request(cls, method: str, url: str, params: Optional[Dict[str, Any]] = None,
                       json: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[
        str, Any]:
        if cls.session is None:
            raise ValueError("Client session is not initialized. Call 'initialize' first.")

        async with cls.session.request(method, url, params=params, json=json, headers=headers) as response:
            response_data = await response.json()
            response_status = response.status
            return {
                "status": response_status,
                "data": response_data
            }

    @classmethod
    async def get(cls, url: str, params: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        return await cls._request("GET", url, params=params, headers=headers)

    @classmethod
    async def post(cls, url: str, json: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        return await cls._request("POST", url, json=json, headers=headers)

    @classmethod
    async def close(cls):
        if cls.session is not None:
            await cls.session.close()
            cls.session = None
