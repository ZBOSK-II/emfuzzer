# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing base of injection sub-tasks.
"""

from abc import ABC, abstractmethod
from enum import StrEnum


class InjectionSubTask(ABC):
    def __init__(self, name: str):
        self._name = name

    def name(self) -> str:
        return self._name

    @abstractmethod
    def inject(self, data: bytes) -> str: ...
    @abstractmethod
    def result_type(self) -> type[StrEnum]: ...


class TypedInjectionSubTask[T: StrEnum](InjectionSubTask):
    @abstractmethod
    def inject(self, data: bytes) -> T: ...
    @abstractmethod
    def result_type(self) -> type[T]: ...
