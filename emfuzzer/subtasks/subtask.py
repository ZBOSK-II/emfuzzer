# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import TypeAlias

from ..results.basic import BasicResult


class SubTask(ABC):
    def __init__(self, name: str):
        self._name = name

    def name(self) -> str:
        return self._name

    @abstractmethod
    def start(self) -> bool: ...

    @abstractmethod
    def finish(self) -> str: ...

    @abstractmethod
    def result_type(self) -> type[StrEnum]: ...


class TypedSubTask[T: StrEnum](SubTask):

    @abstractmethod
    def finish(self) -> T: ...

    @abstractmethod
    def result_type(self) -> type[T]: ...


class BasicSubTask(TypedSubTask[BasicResult]):
    Result: TypeAlias = BasicResult

    def result_type(self) -> type[Result]:
        return self.Result
