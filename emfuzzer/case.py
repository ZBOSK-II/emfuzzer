# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing "case" - an instance of the experiment execution.
"""

from contextlib import contextmanager
from typing import Iterator, Self

from .context import Context
from .results import Results
from .subtasks import SubTasks


class Case:

    def __init__(self, setups: SubTasks, monitoring: SubTasks, checks: SubTasks):
        self._setups = setups
        self._monitoring = monitoring
        self._checks = checks

    @contextmanager
    def execute(self, case_name: str) -> Iterator[None]:
        self._setups.execute_for(case_name)
        with self._monitoring.monitor(case_name):
            yield
        self._checks.execute_for(case_name)

    @classmethod
    def from_config(cls, context: Context, results: Results) -> Self:
        return cls(
            setups=SubTasks.from_config(
                "case", "setups", results=results, context=context
            ),
            checks=SubTasks.from_config(
                "case", "checks", results=results, context=context
            ),
            monitoring=SubTasks.from_config(
                "case", "monitoring", results=results, context=context
            ),
        )
