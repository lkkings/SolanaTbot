# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/1 10:54
@Author     : lkkings
@FileName:  : console_manager.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
from asyncio import Lock
from typing import Optional, Dict

from rich.progress import TaskID, BarColumn, Task, ProgressColumn, TextColumn, DownloadColumn, TransferSpeedColumn, \
    TimeRemainingColumn, Progress as RichProgress,Console
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text
from rich.theme import Theme


class ConsoleManager:
    console = Console(theme=Theme({
        "info": "green",
        "warning": "yellow",
        "error": "bold red"
    }))

    @classmethod
    def print_text(cls, text: str, style: str = "default"):
        """打印普通文本，支持颜色样式"""
        cls.console.print(Text(text, style=style))

    @classmethod
    def print_log(cls, message: str, level: str = "info"):
        """打印格式化的日志信息"""
        if level not in ["info", "warning", "error"]:
            raise ValueError(f"Unsupported log level: {level}")
        cls.console.print(f"[{level}]{level.upper()}: {message}")

    @classmethod
    def print_table(cls, headers: list, rows: list):
        """打印格式化的表格"""
        table = Table(show_header=True, header_style="bold magenta")
        for header in headers:
            table.add_column(header)

        for row in rows:
            table.add_row(*row)

        cls.console.print(table)


class CustomSpinnerColumn(ProgressColumn):
    """
    自定义的指示器列 (Custom spinner columns)
    查看示例 (show expamle): python -m rich.spinner
    """

    DEFAULT_SPINNERS = {
        "waiting": "dots8",
        "starting": "arrow",
        "running": "moon",
        "paused": "smiley",
        "error": "star2",
        "completed": "hearts",
    }

    def __init__(
            self,
            spinner_styles: Optional[Dict[str, str]] = None,
            style: str = "progress.spinner",
            speed: float = 1.0,
    ):
        spinner_styles = spinner_styles or {}
        spinner_names = {
            state: spinner_styles.get(state, default)
            for state, default in self.DEFAULT_SPINNERS.items()
        }
        self.spinners = {
            state: Spinner(spinner_name, style=style, speed=speed)
            for state, spinner_name in spinner_names.items()
        }
        super().__init__()

    def render(self, task: Task):
        t = task.get_time()
        state = task.fields.get("state", "starting")
        spinner = self.spinners.get(state, self.spinners["starting"])
        return spinner.render(t)


class ProgressManager:
    """
    进度管理器 (Progress Manager)
    """

    DEFAULT_COLUMNS = {
        "spinner": CustomSpinnerColumn(),
        "description": TextColumn(
            "{task.description}[bold blue]{task.fields[filename]}"
        ),
        "bar": BarColumn(bar_width=None),
        "percentage": TextColumn("[progress.percentage]{task.percentage:>4.1f}%"),
        "•": "•",
        "speed": TransferSpeedColumn(),
        "remaining": TimeRemainingColumn(),
    }

    def __init__(
            self,
            spinner_column: CustomSpinnerColumn = None,
            custom_columns: Optional[Dict[str, ProgressColumn]] = None,
            bar_width: Optional[int] = None,
            expand: bool = False,
    ):
        chosen_columns_dict = custom_columns or self.DEFAULT_COLUMNS.copy()
        if spinner_column:
            chosen_columns_dict = {"spinner": spinner_column, **chosen_columns_dict}
        if "bar" in chosen_columns_dict and isinstance(
                chosen_columns_dict["bar"], BarColumn
        ):
            bar_column = chosen_columns_dict["bar"]
            bar_column.bar_width = bar_width or 40
        self._progress = RichProgress(
            *chosen_columns_dict.values(), transient=False, expand=expand
        )
        self._progress_lock = Lock()
        self._active_tasks = set()

    def start(self):
        self._progress.start()

    def start_task(self, task_id):
        self._progress.start_task(task_id)

    def stop(self):
        self._progress.stop()

    def stop_task(self, task_id):
        self._progress.stop_task(task_id)

    @property
    def tasks(self):
        return self._progress.tasks

    async def add_task(
            self,
            description: str,
            start: bool = True,
            total: Optional[float] = None,
            completed: int = 0,
            visible: bool = True,
            state: str = "starting",
            filename: str = "",
    ) -> TaskID:
        async with self._progress_lock:
            task_id = self._progress.add_task(
                description=description,
                start=start,
                total=total,
                completed=completed,
                visible=visible,
                filename=filename,
                state=state,
            )
            self._active_tasks.add(task_id)
        return task_id

    async def update(
            self,
            task_id: TaskID,
            total: Optional[float] = None,
            completed: Optional[float] = None,
            advance: Optional[float] = None,
            description: Optional[str] = None,
            visible: bool = True,
            refresh: bool = False,
            filename=None,
            state: Optional[str] = None,
    ) -> None:
        async with self._progress_lock:
            update_params = {
                key: value
                for key, value in [
                    ("advance", advance),
                    ("description", description),
                    ("state", state),
                    ("filename", filename),
                ]
                if value
            }

            self._progress.update(
                task_id,
                total=total,
                completed=completed,
                visible=visible,
                refresh=refresh,
                **update_params,
            )

            if self._progress.tasks[task_id].finished and task_id in self._active_tasks:
                self._active_tasks.remove(task_id)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


async def main():
    async with ProgressManager() as progress:
        pass

if __name__ == '__main__':
    asyncio.run(main())