from abc import ABC, abstractmethod
from enum import StrEnum, auto

from ..Config import Config


class SubTask(ABC):

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


def from_config(config: Config) -> SubTask:
    type = config.get_str("type")
    name = config.get_str("name")
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
