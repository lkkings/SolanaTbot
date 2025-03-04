# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/8/5 2:08
@Author     : lkkings
@FileName:  : __init__.py.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
import os
import time
import logging
import datetime
import traceback
from functools import wraps
import os.path as osp
from typing import Union

from colorama import Fore, Style

from pathlib import Path

from core.constants import *
from utils._singleton import Singleton
from logging.handlers import TimedRotatingFileHandler

# 如果你的文件在项目的子目录下，向上移动到项目根目录
root = osp.dirname(osp.dirname(osp.abspath(__file__)))


class CyberpunkFormatter(logging.Formatter):
    """Custom formatter to add a cyberpunk style to logger messages."""

    def __init__(self):
        super().__init__(datefmt='%Y-%m-%d %H:%M:%S')

    def format(self, record):
        level_color = {
            logging.DEBUG: Fore.LIGHTCYAN_EX + Style.BRIGHT,
            logging.INFO: Fore.LIGHTBLUE_EX + Style.BRIGHT,
            logging.WARNING: Fore.LIGHTYELLOW_EX + Style.BRIGHT,
            logging.ERROR: Fore.LIGHTRED_EX + Style.BRIGHT,
        }

        log_color = level_color.get(record.levelno, Fore.WHITE)
        log_fmt = (
                Fore.LIGHTMAGENTA_EX + '[%(asctime)s]' + Fore.LIGHTBLUE_EX + '[%(name)s]' + log_color + '[%(levelname)s] ' + log_color + " %(message)s" + Style.RESET_ALL)
        formatter = logging.Formatter(log_fmt, datefmt=self.datefmt)
        return formatter.format(record)


class LogManager(metaclass=Singleton):
    def __init__(self, name: str):
        if getattr(self, "_initialized", False):  # 防止重复初始化
            return
        self.name = name
        self.logger = None
        self.log_dir = None
        self._initialized = True

    def setup_logging(self, level=logging.INFO, log_to_console=False, log_path=None):
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(level)
        if self.logger.hasHandlers():
            # logger已经被设置，不做任何操作
            return logger
        self.logger.handlers.clear()
        if log_to_console:
            formatter = CyberpunkFormatter()
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

        if log_path:
            formatter = logging.Formatter(
                fmt='[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            self.log_dir = Path(log_path)
            self.ensure_log_dir_exists(self.log_dir)
            log_file_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S.log")
            log_file = self.log_dir.joinpath(log_file_name)
            fh = TimedRotatingFileHandler(
                log_file, when="midnight", interval=1, backupCount=99, encoding="utf-8"
            )
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

    @staticmethod
    def ensure_log_dir_exists(log_path: Path):
        log_path.mkdir(parents=True, exist_ok=True)

    def clean_logs(self, keep_last_n=10):
        """保留最近的n个日志文件并删除其他文件"""
        if not self.log_dir:
            return
        # self.shutdown()
        all_logs = sorted(self.log_dir.glob("*.logger"))
        if keep_last_n == 0:
            files_to_delete = all_logs
        else:
            files_to_delete = all_logs[:-keep_last_n]
        for log_file in files_to_delete:
            try:
                log_file.unlink()
            except PermissionError:
                self.logger.warning(
                    f"无法删除日志文件 {log_file}, 它正被另一个进程使用"
                )

    def shutdown(self):
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)
        self.logger.handlers.clear()
        time.sleep(1)  # 确保文件被释放


default_log_path = osp.join(root, 'logs')

logger: Union[logging.Logger, None] = None
log_manager: Union[LogManager, None] = None


def log_setup(name, log_to_console=True, level=logging.INFO, log_path=None):
    global log_manager, logger
    if log_path:
        # 创建临时的日志目录
        log_path = Path(log_path)
        log_path.mkdir(exist_ok=True)

    # 初始化日志管理器
    log_manager = LogManager(name)
    log_manager.setup_logging(
        level=level, log_to_console=log_to_console, log_path=log_path
    )
    # 只保留99个日志文件
    log_manager.clean_logs(99)
    logger = log_manager.logger


log_setup(os.getenv('APP_NAME'), level=os.getenv('LEVEL'), log_path=os.getenv('LOG_PATH'))


# 定义装饰器
# 定义接受参数的装饰器
def catch_exceptions(option="", raise_error: bool = True, retry: int = 0):
    """
      装饰器用于捕获同步和异步函数的异常。
      """

    def decorator(func):

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                start_time = time.time()
                result = None
                for i in range(retry + 1):
                    try:
                        result = func(*args, **kwargs)
                        break
                    except:
                        if retry == 0:
                            raise
                speed_time = time.time() - start_time
                logger.debug(f"\n" +
                             f"执行操作: {option} \n" +
                             f"调用同步函数: {func.__name__}\n" +
                             f"执行时间: {speed_time}\n" +
                             f"参数: args={args}, kwargs={kwargs}\n" +
                             f"返回值: {result}")
                # 执行被装饰的函数
                return result
            except Exception as e:
                # 捕获并处理异常
                logger.error(f"\n" +
                             f"执行操作: {option} \n" +
                             f"调用同步函数: {func.__name__}\n" +
                             f"参数: args={args}, kwargs={kwargs}\n" +
                             f"异常: {e}")
                # 可以选择是否抛出异常
                if raise_error:
                    traceback.print_exc()
                    raise e

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                start_time = time.time()
                result = None
                for i in range(retry + 1):
                    try:
                        result = await func(*args, **kwargs)
                        break
                    except:
                        if retry == 0:
                            raise

                speed_time = time.time() - start_time
                logger.debug(f"\n" +
                             f"执行操作: {option} \n" +
                             f"调用异步函数: {func.__name__}\n" +
                             f"执行时间: {speed_time}\n" +
                             f"参数: args={args}, kwargs={kwargs}\n" +
                             f"返回值: {result}")
                # 执行被装饰的函数
                return result
            except Exception as e:
                logger.error(f"\n" +
                             f"执行操作: {option} \n" +
                             f"调用异步函数: {func.__name__}\n" +
                             f"参数: args={args}, kwargs={kwargs}\n" +
                             f"异常: {e}")

                # 可以选择是否抛出异常
                if raise_error:
                    traceback.print_exc()
                    raise e

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
