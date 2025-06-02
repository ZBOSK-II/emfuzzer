# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module holding experiment building blocks - sub tasks.
"""

import logging
from contextlib import contextmanager
from typing import Iterator, Self

from ..config import Config
from ..context import Context
from ..results import Results, ResultsGroup
from .subtask import SubTask

logger = logging.getLogger(__name__)


def subtask_from_config(config: Config, context: Context, *prefix: str) -> SubTask:
    task_type = config.get_str("type")
    name = ".".join(prefix) + "." + config.get_str("name")
    args = config.section("args")
    match task_type:
        case "subprocess":
            # pylint: disable=import-outside-toplevel
            from .subprocess import Subprocess

            return Subprocess.from_config(name, args, context)
        case "ping_stable":
            from .ping import PingIsStable  # pylint: disable=import-outside-toplevel

            return PingIsStable.from_config(name, args, context)
        case "ping_alive":
            from .ping import PingIsAlive  # pylint: disable=import-outside-toplevel

            return PingIsAlive.from_config(name, args, context)
        case "remote":
            from .remote import Remote  # pylint: disable=import-outside-toplevel

            return Remote.from_config(name, args)
        case "coap_monitor":
            # pylint: disable=import-outside-toplevel
            from ..coap import CoapMonitor

            return CoapMonitor.from_config(name, args, context)
        case _:
            raise ValueError(f"Unknown sub-task type '{task_type}'")


class SubTaskExecution:
    def __init__(self, task: SubTask, results: ResultsGroup):
        self._task = task
        self._results = results
        self._start_result: SubTask.StartResult | None = None

    def name(self) -> str:
        return self._task.name()

    def start(self) -> None:
        self._start_result = self._task.start()

    def finish_for(self, key: str) -> None:
        assert self._start_result is not None
        result = (
            self._task.finish()
            if isinstance(self._start_result, SubTask.StartedType)
            else self._start_result
        )
        self._results.collect(key, result)
        self._start_result = None

    def execute_for(self, key: str) -> None:
        self.start()
        self.finish_for(key)


class SubTasks:
    def __init__(self, results: Results, *prefix: str):
        self._results = results
        self._prefix = prefix
        self._tasks: list[SubTaskExecution] = []

    def name(self) -> str:
        return ".".join(self._prefix)

    def register(self, task: SubTask) -> None:
        logger.info(f"Registering <{task.name()}>")
        execution = SubTaskExecution(
            task,
            self._results.register(task.name(), task.result_type()),
        )
        self._tasks.append(execution)

    def execute_for(self, key: str) -> None:
        logger.info(f"Start {self.name()}")
        for task in self._tasks:
            logger.info(f"Executing {task.name()}")
            task.execute_for(key)
        logger.info(f"End {self.name()}")

    @contextmanager
    def monitor(self, key: str) -> Iterator[None]:
        try:
            self.start_all()
            yield
        finally:
            self.finish_all_for(key)

    def start_all(self) -> None:
        logger.info(f"Starting {self.name()}")
        for task in self._tasks:
            logger.info(f"Starting {task.name()}")
            task.start()
        logger.info(f"All {self.name()} started")

    def finish_all_for(self, key: str) -> None:
        logger.info(f"Finishing {self.name()}")
        for task in self._tasks:
            logger.info(f"Finishing {task.name()}")
            task.finish_for(key)
        logger.info(f"All {self.name()} finished")

    @classmethod
    def from_config(cls, *prefix: str, results: Results, context: Context) -> Self:
        tasks = cls(results, *prefix)
        for conf in context.config_root.get_config_list(*prefix):
            tasks.register(subtask_from_config(conf, context, *prefix))
        return tasks
