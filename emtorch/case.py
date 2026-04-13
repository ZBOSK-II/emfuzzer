# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing "case" - an instance of the experiment execution.
"""

from typing import Self

from .config import Config
from .context import CaseContext, Context
from .delay import Delay
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

    def execute(self, context: CaseContext) -> None:
        self._setups.execute_for(context)
        with self._monitoring.monitor(context):
            self._delays.wait_before_actions()
            self._actions.execute_for(context)
        self._checks.execute_for(context)

    def wait_between_cases(self) -> None:
        self._delays.wait_between_cases()

    @classmethod
    def from_config(cls, context: Context) -> Self:
        return cls(
            delays=CaseDelays.from_config("case", "delays", config=context.config_root),
            setups=SubTasks.from_config("case", "setups", context=context),
            checks=SubTasks.from_config("case", "checks", context=context),
            monitoring=SubTasks.from_config("case", "monitoring", context=context),
            actions=SubTasks.from_config("case", "actions", context=context),
        )
