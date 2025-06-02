# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing experiment results.
"""

import sys
from collections import defaultdict
from datetime import datetime
from enum import StrEnum
from typing import Any, Collection, Mapping

from ..config import Config
from ..version import VERSION


class ResultsGroup:

    def __init__(self, results_names: list[str], success: str) -> None:
        self.data: dict[str, list[str]] = {}
        for result in results_names:
            self.data[result] = []

        self.success = success

        self.failed_keys: dict[str, str] = {}

    def collect(self, key: str, result: str) -> None:
        self.data[result].append(key)
        if result != self.success:
            self.failed_keys[key] = result

    def total(self) -> int:
        return sum(len(v) for v in self.data.values())

    def total_errors(self) -> int:
        return len(self.failed_keys)

    def summary(self, indent: str = "\t") -> str:
        return "\n".join(f"{indent}{k}: {len(v)}" for k, v in self.data.items())

    def to_dict(self) -> dict[str, list[str]]:
        return self.data

    def to_failed_keys_dict(self) -> dict[str, str]:
        return self.failed_keys


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

    def register(self, group: str, results: type[StrEnum]) -> ResultsGroup:
        r = list(str(item) for item in results)
        g = ResultsGroup(r, r[0])
        if group in self.data:
            raise RuntimeError(
                f"Result group already defined: '{group}'. Probably duplicated name. "
            )
        self.data[group] = g
        return g

    def add_key(self, key: str) -> None:
        self.keys.append(key)

    def finish(self) -> None:
        self.info["end"] = self.__iso_timestamp()

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

    def failed_keys(self) -> dict[str, list[str]]:
        result = defaultdict(list)
        for g, d in self.data.items():
            for k, v in d.to_failed_keys_dict().items():
                result[k].append(g + "." + v)
        return dict(result)

    def to_dict(self) -> Mapping[str, Collection[Any]]:
        return (
            {"info": self.info}
            | {"all": self.keys}
            | {"failed": self.failed_keys()}
            | {"groups": {k: v.to_dict() for k, v in self.data.items()}}
        )

    @staticmethod
    def __iso_timestamp() -> str:
        return datetime.now().astimezone().isoformat()
