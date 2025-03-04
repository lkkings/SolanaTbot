# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/13 7:55
@Author     : lkkings
@FileName:  : helius.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from typing import Dict, Any, List, Union
from urllib.parse import urljoin

from core.base_client import Client
from core.constants import HELIUS
from core.types.event import EventType
from logger import catch_exceptions


class HeliusClient(Client):

    async def send_json_request(self, endpoint: str, method='GET', json: Dict = None) -> Union[Dict[str, Any], List]:
        params = {'api-key': HELIUS.API_KEY}
        url = urljoin(HELIUS.HOST, endpoint)
        data = await self.make_request(url, method=method, params=params, json=json)
        if 'error' in data:
            if 'message' in data['error']:
                error_msg = data['error']['message']
            else:
                error_msg = data['error']
            raise Exception(f'Helius API异常=>{error_msg}')
        return data

    @catch_exceptions(option='创建WebHook')
    async def create_webhook(
            self,
            account_addresses: List[str],
            transaction_types: List[EventType] = None,
            webhook_type: str = HELIUS.WEBHOOK_TYPE,
            webhook_url: str = HELIUS.WEBHOOK,
            auth_header: str = HELIUS.AUTH_HEADER,
            cover: bool = HELIUS.COVER_WEBHOOK,
    ) -> Dict[str, Any]:
        """
         api文档参考：https://docs.helius.dev/webhooks-and-websockets/api-reference/create-webhook
        通过向 Helius API 发起 POST 请求来创建一个 webhook。
        :param webhook_url: webhook 接收事件的 URL。
        :param transaction_types: 订阅的交易类型列表。交易类型的枚举值。
        :param account_addresses: 包含在 webhook 中的账户地址列表。
        :param webhook_type: webhook 的类型。
        :param auth_header: API 请求的授权头信息，例如 'Bearer YOUR_AUTH_TOKEN'。
        :param cover: 是否覆盖已经存在的webhook
        :return: API 响应的 JSON 数据，包含创建的 webhook 的详细信息。
        """
        webhooks = await self.get_all_webhooks()
        if len(webhooks) > 0:
            if cover:
                await self.delete_webhook(webhooks[0]['webhookID'])
            else:
                return webhooks[0]
        if transaction_types is None:
            transaction_types = [EventType.ANY.name]
        else:
            transaction_types = [transaction_type.name for transaction_type in transaction_types]
        payload = {
            'webhookURL': webhook_url,
            'transactionTypes': transaction_types,
            'accountAddresses': account_addresses,
            'webhookType': webhook_type,
            "authHeader": auth_header
        }
        return await self.send_json_request('/v0/webhooks', method='POST', json=payload)

    @catch_exceptions(option='获取所有WebHook的详细信息')
    async def get_all_webhooks(self) -> List[Dict[str, Any]]:
        """
         api文档参考：https://docs.helius.dev/webhooks-and-websockets/api-reference/get-all-webhooks
        :return: 返回所有 webhook 的详细信息
        """
        return await self.send_json_request('/v0/webhooks', method='GET')

    @catch_exceptions(option='获取指定WebHook的详细信息')
    async def get_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """
         api文档参考：https://docs.helius.dev/webhooks-and-websockets/api-reference/get-webhook
        :param webhook_id: 返回的webhook ID eg: c73e75c2-a669-4bd0-b3f8-9cf0b7d86ad8
        :return: 指定webhook 的详细信息
        """
        return await self.send_json_request(f'/v0/webhooks/{webhook_id}', method='GET')

    @catch_exceptions(option='删除WebHook')
    async def delete_webhook(self, webhook_id: str):
        params = {'api-key': HELIUS.API_KEY}
        url = urljoin(HELIUS.HOST, f'/v0/webhooks/{webhook_id}')
        await self._session.request(url=url, params=params, method='DELETE')


helius_client = HeliusClient()
