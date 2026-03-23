# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing "case" - an instance of the experiment execution.
"""

from contextlib import contextmanager
from typing import Iterator, Self

from .config import Config
from .context import Context
from .delay import Delay
from .results import Results
from .subtasks import SubTasks


class CaseDelays:
    def __init__(self, between_cases: Delay, before_actions: Delay):
        self._between_cases = between_cases
        self._before_actions = before_actions

    def wait_before_actions(self) -> None:
        self._before_actions.wait()

    def wait_between_cases(self) -> None:
        self._between_cases.wait()

    @classmethod
    def from_config(cls, *prefix: str, config: Config) -> Self:
        return cls(
            between_cases=Delay.from_config(*prefix, "between_cases", config=config),
            before_actions=Delay.from_config(*prefix, "before_actions", config=config),
        )


class Case:

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        delays: CaseDelays,
        setups: SubTasks,
        monitoring: SubTasks,
        checks: SubTasks,
        actions: SubTasks,
    ):
        self._delays = delays
        self._setups = setups
        self._monitoring = monitoring
        self._checks = checks
        self._actions = actions

    @contextmanager
    def execute(self, case_name: str) -> Iterator[None]:
        self._setups.execute_for(case_name)
        with self._monitoring.monitor(case_name):
            self._delays.wait_before_actions()
            self._actions.execute_for(case_name)
            yield
        self._checks.execute_for(case_name)

    def wait_between_cases(self) -> None:
        self._delays.wait_between_cases()

    @classmethod
    def from_config(cls, context: Context, results: Results) -> Self:
        return cls(
            delays=CaseDelays.from_config("case", "delays", config=context.config_root),
            setups=SubTasks.from_config(
                "case", "setups", results=results, context=context
            ),
            checks=SubTasks.from_config(
                "case", "checks", results=results, context=context
            ),
            monitoring=SubTasks.from_config(
                "case", "monitoring", results=results, context=context
            ),
            actions=SubTasks.from_config(
                "case", "actions", results=results, context=context
            ),
        )
