import logging
from typing import Self

from .Config import Config
from .Results import Results, ResultsGroup
from .subtasks import SubTask
from .subtasks import from_config as subtask_from_config

logger = logging.getLogger(__name__)


class Check:

    def __init__(self, subtask: SubTask, results: ResultsGroup):
        self.subtask = subtask
        self.results = results

    def name(self) -> str:
        return self.subtask.name()

    def perform_for(self, key: str) -> None:
        self.results.collect(key, self.subtask.run())


class Checks:
    def __init__(self, results: Results):
        self.results = results
        self.checks: list[Check] = []

    def register(self, subtask: SubTask) -> None:
        logger.info(f"Registering <{subtask.name()}>")
        check = Check(
            subtask,
            self.results.register(
                subtask.name(), SubTask.Result, SubTask.Result.SUCCESS
            ),
        )
        self.checks.append(check)

    def perform_for(self, key: str) -> None:
        for check in self.checks:
            logger.info(f"Checking {check.name()}")
            check.perform_for(key)

    @classmethod
    def from_config(cls, results: Results, config: Config) -> Self:
        checks = cls(results)
        for conf in config.get_config_list("checks"):
            checks.register(subtask_from_config(conf))
        return checks
