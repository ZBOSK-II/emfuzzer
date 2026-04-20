# Copyright (c) 2025-2026 Warsaw University of Technology
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


class SubTaskResults:

    def __init__(self, results_names: list[str], success: str) -> None:
        self.subtasks: dict[str, list[str]] = {}
        for result in results_names:
            self.subtasks[result] = []

        self.success = success

        self.failed_case_ids: dict[str, str] = {}

    def collect(self, identifier: str, result: str) -> None:
        self.subtasks[result].append(identifier)
        if result != self.success:
            self.failed_case_ids[identifier] = result

    def total(self) -> int:
        return sum(len(v) for v in self.subtasks.values())

    def total_errors(self) -> int:
        return len(self.failed_case_ids)

    def summary(self, indent: str = "\t") -> str:
        return "\n".join(f"{indent}{k}: {len(v)}" for k, v in self.subtasks.items())

    def to_dict(self) -> dict[str, list[str]]:
        return self.subtasks

    def to_failed_ids_dict(self) -> dict[str, str]:
        return self.failed_case_ids


class Results:

    def __init__(self, config: Config):
        self.subtasks: dict[str, SubTaskResults] = {}
        self.cases: list[str] = []
        self.info = {
            "version": VERSION,
            "args": " ".join(sys.argv[1:]),
            "config": config.to_dict(),
            "start": self.__iso_timestamp(),
        }

    def register(self, name: str, results: type[StrEnum]) -> SubTaskResults:
        r = list(str(item) for item in results)
        s = SubTaskResults(r, r[0])
        if name in self.subtasks:
            raise RuntimeError(
                f"Subtask results already registered: '{name}'. Probably duplicated name."
            )
        self.subtasks[name] = s
        return s

    def add_case(self, identifier: str) -> None:
        self.cases.append(identifier)

    def finish(self) -> None:
        self.info["end"] = self.__iso_timestamp()

    def __getitem__(self, name: str) -> SubTaskResults:
        return self.subtasks[name]

    def summary(self) -> str:
        header = f"Processed: {len(self.cases)}\n"
        return header + "\n".join(
            f"{k} ({v.total_errors()}/{v.total()}):\n{v.summary()}"
            for k, v in self.subtasks.items()
        )

    def total_errors(self) -> int:
        return sum(g.total_errors() for g in self.subtasks.values())

    def failed_case_ids(self) -> dict[str, list[str]]:
        result = defaultdict(list)
        for g, d in self.subtasks.items():
            for k, v in d.to_failed_ids_dict().items():
                result[k].append(g + "." + v)
        return dict(result)

    def to_dict(self) -> Mapping[str, Collection[Any]]:
        return (
            {"info": self.info}
            | {
                "cases": {
                    "all": self.cases,
                    "failed": self.failed_case_ids(),
                }
            }
            | {"subtasks": {k: v.to_dict() for k, v in self.subtasks.items()}}
        )

    @staticmethod
    def __iso_timestamp() -> str:
        return datetime.now().astimezone().isoformat()
