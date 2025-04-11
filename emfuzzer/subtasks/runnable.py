# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

from abc import ABC, abstractmethod
from enum import StrEnum, auto


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
