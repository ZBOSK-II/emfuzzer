# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

import logging
from typing import Self

from ..config import Config
from ..results import Results, ResultsGroup
from .runnable import Runnable

logger = logging.getLogger(__name__)


def runnable_from_config(config: Config, *prefix: str) -> Runnable:
    runnable_type = config.get_str("type")
    name = ".".join(prefix) + "." + config.get_str("name")
    args = config.section("args")
    match runnable_type:
        case "subprocess":
            # pylint: disable=import-outside-toplevel
            from .subprocess import Subprocess

            return Subprocess.from_config(name, args)
        case "ping_stable":
            from .ping import PingIsStable  # pylint: disable=import-outside-toplevel

            return PingIsStable.from_config(name, args)
        case "ping_alive":
            from .ping import PingIsAlive  # pylint: disable=import-outside-toplevel

            return PingIsAlive.from_config(name, args)
        case _:
            raise ValueError(f"Unknown sub-task type '{runnable_type}'")


class SubTask:
    def __init__(self, runnable: Runnable, results: ResultsGroup):
        self.runnable = runnable
        self.results = results

    def name(self) -> str:
        return self.runnable.name()

    def execute_for(self, key: str) -> None:
        self.results.collect(key, self.runnable.run())


class SubTasks:
    def __init__(self, results: Results, *prefix: str):
        self.results = results
        self.prefix = prefix
        self.tasks: list[SubTask] = []

    def name(self) -> str:
        return ".".join(self.prefix)

    def register(self, runnable: Runnable) -> None:
        logger.info(f"Registering <{runnable.name()}>")
        task = SubTask(
            runnable,
            self.results.register(
                runnable.name(), Runnable.Result, Runnable.Result.SUCCESS
            ),
        )
        self.tasks.append(task)

    def execute_for(self, key: str) -> None:
        logger.info(f"Start {self.name()}")
        for task in self.tasks:
            logger.info(f"Executing {task.name()}")
            task.execute_for(key)
        logger.info(f"End {self.name()}")

    @classmethod
    def from_config(cls, *prefix: str, results: Results, config: Config) -> Self:
        tasks = cls(results, *prefix)
        for conf in config.get_config_list(*prefix):
            tasks.register(runnable_from_config(conf, *prefix))
        return tasks
