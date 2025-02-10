import logging
from abc import ABC, abstractmethod
from enum import StrEnum, auto
from typing import Self

from ..Config import Config
from ..Results import Results, ResultsGroup

logger = logging.getLogger(__name__)


class Runnable(ABC):

    class Result(StrEnum):
        SUCCESS = auto()
        FAILURE = auto()
        TIMEOUT = auto()
        ERROR = auto()

    def __init__(self, name: str):
        self._name = name

    def name(self) -> str:
        return self._name

    @abstractmethod
    def run(self) -> Result: ...


def runnable_from_config(config: Config, *prefix: str) -> Runnable:
    type = config.get_str("type")
    name = ".".join(prefix) + "." + config.get_str("name")
    args = config.section("args")
    match type:
        case "subprocess":
            from .Subprocess import Subprocess

            return Subprocess.from_config(name, args)
        case "pinger":
            from .Pinger import Pinger

            return Pinger.from_config(name, args)
        case _:
            raise ValueError(f"Unknown sub-task type '{type}'")


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
        for task in self.tasks:
            logger.info(f"Executing {task.name()}")
            task.execute_for(key)

    @classmethod
    def from_config(cls, *prefix: str, results: Results, config: Config) -> Self:
        tasks = cls(results, *prefix)
        for conf in config.get_config_list(*prefix):
            tasks.register(runnable_from_config(conf, *prefix))
        return tasks
