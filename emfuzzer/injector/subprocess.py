# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing subprocess based injection sub-task.
"""

import logging
from typing import Self

from ..config import Config
from ..context import Context
from ..io import IOLoop
from ..io.streams import StreamWriter
from ..results.basic import BasicResult
from ..subtasks.subprocess import FinishConfig
from ..subtasks.subprocess import Subprocess as SubprocessTask
from .subtask import TypedInjectionSubTask

logger = logging.getLogger(__name__)


class Subprocess(TypedInjectionSubTask[BasicResult]):
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self, name: str, args: list[str], shell: bool, timeout: float, io: IOLoop
    ):
        super().__init__(name)

        self._task = SubprocessTask(
            name=self.name(),
            args=args,
            shell=shell,
            finish_config=FinishConfig(timeout, None),
            io=io,
        )

    def inject(self, data: bytes) -> BasicResult:
        if not self._task.basic_start():
            return BasicResult.NOT_STARTED

        assert self._task.process is not None
        assert self._task.process.stdin is not None
        self._task.io.register(
            StreamWriter(f"<{self.name()}> - STDIN", self._task.process.stdin, data)
        )

        return self._task.finish()

    def result_type(self) -> type[BasicResult]:
        return BasicResult

    @classmethod
    def from_config(cls, name: str, config: Config, context: Context) -> Self:
        return cls(
            name=name,
            args=config.get_str_list("cmd"),
            shell=config.get_bool("shell"),
            timeout=config.get_float("timeout"),
            io=context.worker(IOLoop),
        )
