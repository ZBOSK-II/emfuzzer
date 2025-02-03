import sys
from datetime import datetime
from enum import StrEnum
from typing import Any, Collection, Mapping

from .Config import Config
from .Version import VERSION


class ResultsGroup:

    def __init__(self, keys: list[str], success_key: str) -> None:
        self.data: dict[str, list[str]] = {}
        for k in keys:
            self.data[k] = []

        self.success_key = success_key

    def collect(self, key: str, result: str) -> None:
        self.data[result].append(key)

    def total(self) -> int:
        return sum(len(v) for v in self.data.values())

    def total_errors(self) -> int:
        return sum(len(v) for k, v in self.data.items() if k != self.success_key)

    def summary(self, indent: str = "\t") -> str:
        return "\n".join(f"{indent}{k}: {len(v)}" for k, v in self.data.items())

    def to_dict(self) -> dict[str, list[str]]:
        return self.data


class Results:

    def __init__(self, config: Config):
        self.data: dict[str, ResultsGroup] = {}
        self.keys: list[str] = []
        self.info = {
            "version": VERSION,
            "args": " ".join(sys.argv[1:]),
            "config": config.to_dict(),
            "start": self.__iso_timestamp(),
        }
        self.extra: dict[str, int] = {}

    def register(
        self, group: str, results: type[StrEnum], success: StrEnum
    ) -> ResultsGroup:
        g = ResultsGroup([k for k in results], success)
        self.data[group] = g
        return g

    def add_key(self, key: str) -> None:
        self.keys.append(key)

    def finish(self, extra: dict[str, int]) -> None:
        self.info["end"] = self.__iso_timestamp()
        self.extra = extra

    def __getitem__(self, group: str) -> ResultsGroup:
        return self.data[group]

    def summary(self) -> str:
        header = f"Sent: {len(self.keys)}\n"
        return header + "\n".join(
            f"{k} ({v.total_errors()}/{v.total()}):\n{v.summary()}"
            for k, v in self.data.items()
        )

    def total_errors(self) -> int:
        return sum(g.total_errors() for g in self.data.values())

    def to_dict(self) -> Mapping[str, Collection[Any]]:
        return (
            {"info": self.info}
            | {k: v.to_dict() for k, v in self.data.items()}
            | {"all": self.keys}
            | {"extra": self.extra}
        )

    @staticmethod
    def __iso_timestamp() -> str:
        return datetime.now().astimezone().isoformat()
