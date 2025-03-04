# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/15 19:24
@Author     : lkkings
@FileName:  : demo.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/7 20:24
@Author     : lkkings
@FileName:  : add_pool_task.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from dataclasses import dataclass
from core.base_task import TaskParams, AsyncTask, TaskPayload, V
from logger import catch_exceptions


@dataclass
class Params(TaskParams):
    pass


@dataclass
class Payload(TaskPayload):
    pass


class Task(AsyncTask[V]):
    @catch_exceptions(option='')
    async def run(self, params: Params) -> Payload:
        pass
