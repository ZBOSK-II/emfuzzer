# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module containing base building blocks of the experiment - sub tasks.
"""

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import TypeAlias

from ..results.basic import BasicResult


class SubTask(ABC):
    # pylint: disable=too-few-public-methods
    class StartedType:
        pass

    type StartResult = str | StartedType
    STARTED = StartedType()

    def __init__(self, name: str):
        self._name = name

    def name(self) -> str:
        return self._name

    @abstractmethod
    def start(self) -> str | StartedType: ...

    @abstractmethod
    def finish(self) -> str: ...

    @abstractmethod
    def result_type(self) -> type[StrEnum]: ...


class TypedSubTask[T: StrEnum](SubTask):

    @abstractmethod
    def start(self) -> T | SubTask.StartedType: ...

    @abstractmethod
    def finish(self) -> T: ...

    @abstractmethod
    def result_type(self) -> type[T]: ...


class BasicSubTask(TypedSubTask[BasicResult]):
    type StartResult = BasicResult | SubTask.StartedType
    Result: TypeAlias = BasicResult

    def start(self) -> StartResult:
        return SubTask.STARTED if self.basic_start() else BasicResult.NOT_STARTED

    @abstractmethod
    def basic_start(self) -> bool: ...

    def result_type(self) -> type[Result]:
        return self.Result
