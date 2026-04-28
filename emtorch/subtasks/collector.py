# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing value collector.
"""

import logging
import re
from abc import abstractmethod
from typing import Self

from ..case.instance import CaseId
from ..config import Config
from ..context import CaseContext, Context
from ..results.values import TypedValue
from .subtask import BasicSubTask


class Collector[T: (int | float)]:

    def __init__(self, value: TypedValue[T]):
        self._value = value
        self._current_value: None | T = None

    def commit(self, case_id: CaseId) -> None:
        if self._current_value is not None:
            self._value.collect(case_id, self._current_value)
            self._current_value = None

    def set_current(self, value: T) -> None:
        self._current_value = value

    def has_value(self) -> bool:
        return self._current_value is not None

    @classmethod
    def create(cls, name: str, context: Context) -> Self:
        value = TypedValue[T]()
        context.results.register_value(name, value)
        return cls(value)


class LoggerMatcher[T: (int | float)](BasicSubTask):
    def __init__(self, name: str, collector: Collector[T], pattern: str, subtask: str):
        super().__init__(name, logging.getLogger(__name__))

        self._collector = collector
        self._regex = re.compile(pattern)
        self._error = False
        self._case_id: CaseId | None = None

        def log_filter(r: logging.LogRecord) -> bool:
            if r.__dict__.get("subtask") == subtask:
                match = self._regex.search(r.getMessage())
                if match is not None:
                    try:
                        self.extract_value(match.group("value"))
                        self._error = False
                    except ValueError:
                        self._error = True
            return True

        self._filter = log_filter

    @abstractmethod
    def extract_value(self, value: str) -> None:
        pass

    def basic_start(self, context: CaseContext) -> bool:
        root_logger = logging.getLogger()
        root_logger.handlers[0].addFilter(self._filter)
        self._case_id = context.case.identifier
        return True

    def finish(self) -> BasicSubTask.Result:
        assert self._case_id

        root_logger = logging.getLogger()
        root_logger.handlers[0].removeFilter(self._filter)

        if self._error:
            return self.Result.ERROR
        if self._collector.has_value():
            self._collector.commit(self._case_id)
            return self.Result.SUCCESS
        return self.Result.FAILURE

    @classmethod
    def from_config(cls, name: str, config: Config, context: Context) -> Self:
        return cls(
            name=name,
            collector=Collector[T].create(config.get_str("value"), context),
            pattern=config.get_str("pattern"),
            subtask=config.get_str("subtask"),
        )


class LoggerIntMatcher(LoggerMatcher[int]):
    def extract_value(self, value: str) -> None:
        self._collector.set_current(int(value))


class LoggerFloatMatcher(LoggerMatcher[float]):
    def extract_value(self, value: str) -> None:
        self._collector.set_current(float(value))
