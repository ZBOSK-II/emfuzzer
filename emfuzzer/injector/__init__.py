# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing injection part of the experiment.
"""

from typing import Self

from ..config import Config
from ..context import Context
from ..results import Results
from .subtask import InjectionSubTask


def subtask_from_config(config: Config, context: Context) -> InjectionSubTask:
    task_type = config.get_str("type")
    name = f"injection.{task_type}"
    args = config.section("args")
    match task_type:
        case "coap":
            # pylint: disable=import-outside-toplevel
            from ..coap import CoapInjector

            return CoapInjector.from_config(name, args, context)
        case "subprocess":
            # pylint: disable=import-outside-toplevel
            from .subprocess import Subprocess

            return Subprocess.from_config(name, args, context)
        case _:
            raise ValueError(f"Unknown sub-task type '{task_type}'")


class Injector:

    def __init__(self, results: Results, task: InjectionSubTask):
        self._results = results.register(task.name(), task.result_type())
        self._task = task

    def inject(self, key: str, data: bytes) -> None:
        self._results.collect(key, self._task.inject(data))

    @classmethod
    def from_config(cls, results: Results, context: Context) -> Self:
        return cls(
            results,
            subtask_from_config(context.config_root.section("injector"), context),
        )
