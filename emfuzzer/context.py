# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing context of the experiment.
"""

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self, cast

from .config import Config


class Worker(ABC):
    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...


class Context:

    def __init__(self, config: Config) -> None:
        self._workers: dict[type[Worker], Worker] = {}
        self._data: dict[str, object] = {}
        self._config = config

    @property
    def config_root(self) -> Config:
        return self._config

    def worker[T: Worker](self, worker: type[T]) -> T:
        if instance := self._workers.get(worker):
            return cast(T, instance)

        instance = worker()
        instance.start()

        self._workers[worker] = instance

        return instance

    def teardown(self) -> None:
        for w in self._workers.values():
            w.stop()

        self._workers.clear()

    def register_data(self, name: str, item: object) -> None:
        if name in self._data:
            raise RuntimeError(f"Data already registered: '{name}'")

        self._data[name] = item

    def data[T](self, data_type: type[T], name: str) -> T:
        if item := self._data.get(name):
            if isinstance(item, data_type):
                return item
            raise RuntimeError(f"Invalid data type for: '{name}'")
        raise RuntimeError(f"Unknown data: '{name}'")

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_traceback: TracebackType | None,
    ) -> None:
        self.teardown()
