# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

import logging
from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import StrEnum, auto
from typing import Iterator, Self

from ..Config import Config
from ..Results import Results, ResultsGroup

logger = logging.getLogger(__name__)


class Monitor(ABC):

    class Result(StrEnum):
        SUCCESS = auto()
        NOT_STARTED = auto()
        FAILURE = auto()
        TIMEOUT = auto()
        ERROR = auto()

    def __init__(self, name: str):
        self._name = name

    def name(self) -> str:
        return self._name

    @abstractmethod
    def start(self) -> bool: ...

    @abstractmethod
    def finish(self) -> Result: ...


def monitor_from_config(config: Config, *prefix: str) -> Monitor:
    type = config.get_str("type")
    name = ".".join(prefix) + "." + config.get_str("name")
    args = config.section("args")
    match type:
        case "remote":
            from .Remote import Remote

            return Remote.from_config(name, args)
        case _:
            raise ValueError(f"Unknown monitor type '{type}'")


class MonitorTask:
    def __init__(self, monitor: Monitor, results: ResultsGroup):
        self.monitor = monitor
        self.results = results
        self.started = False

    def name(self) -> str:
        return self.monitor.name()

    def start(self) -> None:
        self.started = self.monitor.start()

    def finish_for(self, key: str) -> None:
        result = self.monitor.finish() if self.started else Monitor.Result.NOT_STARTED
        self.results.collect(key, result)
        self.started = False


class Monitoring:
    def __init__(self, results: Results, *prefix: str):
        self.results = results
        self.prefix = prefix
        self.tasks: list[MonitorTask] = []

    def name(self) -> str:
        return ".".join(self.prefix)

    def register(self, monitor: Monitor) -> None:
        logger.info(f"Registering <{monitor.name()}>")
        task = MonitorTask(
            monitor,
            self.results.register(
                monitor.name(), Monitor.Result, Monitor.Result.SUCCESS
            ),
        )
        self.tasks.append(task)

    @contextmanager
    def monitor(self, key: str) -> Iterator[None]:
        try:
            self.start_all()
            yield
        finally:
            self.finish_all_for(key)

    def start_all(self) -> None:
        logger.info(f"Starting {self.name()}")
        for task in self.tasks:
            logger.info(f"Starting {task.name()}")
            task.start()
        logger.info(f"All {self.name()} started")

    def finish_all_for(self, key: str) -> None:
        logger.info(f"Finishing {self.name()}")
        for task in self.tasks:
            logger.info(f"Finishing {task.name()}")
            task.finish_for(key)
        logger.info(f"All {self.name()} finished")

    @classmethod
    def from_config(cls, *prefix: str, results: Results, config: Config) -> Self:
        tasks = cls(results, *prefix)
        for conf in config.get_config_list(*prefix):
            tasks.register(monitor_from_config(conf, *prefix))
        return tasks
