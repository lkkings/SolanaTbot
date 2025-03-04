# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/7 19:28
@Author     : lkkings
@FileName:  : task.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
from asyncio import Future
from core.base_task import AsyncTask, TaskResp, V
from core.constants import MAX_THREAD_NUM


class Worker:
    def __init__(self, max_thread_num=MAX_THREAD_NUM):
        self._running = False
        self._t = None

        self._task_queue = asyncio.PriorityQueue()
        self._semaphore = asyncio.Semaphore(max_thread_num)

    @property
    def running(self):
        return self._running

    def run_task(self, task: AsyncTask[V]) -> Future[TaskResp[V]]:
        future = asyncio.Future()
        task.set_future(future)
        self._task_queue.put_nowait(task)
        return future

    async def run(self):
        self._running = True
        while self._running:
            task = await self._task_queue.get()
            if task is None:
                break

            def callback(_future):
                self._semaphore.release()

            await self._semaphore.acquire()
            _task = asyncio.create_task(task.exec())
            _task.add_done_callback(callback)

    async def start(self):
        self._t = asyncio.create_task(self.run())

    async def join(self):
        await self._t

    async def stop(self):
        self._running = False
        await self._task_queue.put(None)
        await self.join()


worker = Worker()
