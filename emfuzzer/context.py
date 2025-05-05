# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self


class Worker(ABC):
    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...


class Context:

    def __init__(self) -> None:
        self._workers: dict[type[Worker], Worker] = {}

    def worker(self, worker: type[Worker]) -> Worker:
        if instance := self._workers.get(worker):
            return instance

        instance = worker()
        instance.start()

        self._workers[worker] = instance

        return instance

    def teardown(self) -> None:
        for w in self._workers.values():
            w.stop()

        self._workers.clear()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_traceback: TracebackType | None,
    ) -> None:
        self.teardown()
