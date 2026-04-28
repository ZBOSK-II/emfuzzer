# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Subpackage representing context of the experiment.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self, cast

from ..case.instance import CaseInstance
from ..config import Config
from ..results import Results


class Worker(ABC):
    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass


class Context:

    def __init__(self, config: Config):
        self._workers: dict[type[Worker], Worker] = {}
        self._data: dict[str, object] = {}
        self._config = config
        self._results = Results(config)

    @property
    def config_root(self) -> Config:
        return self._config

    @property
    def results(self) -> Results:
        return self._results

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

    def enter_case(self, case: CaseInstance) -> "CaseContext":
        return CaseContext(self, case)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_traceback: TracebackType | None,
    ) -> None:
        self.results.finish()
        self.teardown()


class CaseContext:
    def __init__(self, parent: Context, case: CaseInstance):
        self._parent = parent
        self._case = case

        self.results.add_case(self.case.identifier)

    @property
    def parent(self) -> Context:
        return self._parent

    @property
    def case(self) -> CaseInstance:
        return self._case

    @property
    def results(self) -> Results:
        return self._parent.results

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_traceback: TracebackType | None,
    ) -> None:
        pass


__all__ = ["Context", "CaseContext", "Worker"]
