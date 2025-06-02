# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing remote (SSH) task as sub-tasks.
"""

import logging
from typing import Self

from ..config import Config
from ..ssh import ConnectionConfig, Invoker
from .subprocess import FinishConfig
from .subtask import BasicSubTask

logger = logging.getLogger(__name__)


class Remote(BasicSubTask):
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        name: str,
        command: str,
        start_key: str,
        connection_config: ConnectionConfig,
        start_timeout: float,
        finish_config: FinishConfig,
    ):
        super().__init__(name)
        self.invoker = Invoker(
            name=name,
            command=command,
            connection_config=connection_config,
            start_key=start_key,
        )
        self.start_timeout = start_timeout
        self.finish_config = finish_config

    def basic_start(self) -> bool:
        try:
            self.invoker.open()
            if not self.invoker.wait_for_start(self.start_timeout):
                self.invoker.close()
                return False
            return True
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.error(f"Failed to start monitoring <{self.name()}>: {ex}")
            return False

    def finish(self) -> BasicSubTask.Result:
        try:
            if self.finish_config.signal:
                self.invoker.signal(self.finish_config.signal)
            result = self.invoker.wait_for_exit(self.finish_config.timeout)
            self.invoker.close()
            return self.Result.SUCCESS if (result == 0) else self.Result.FAILURE
        except TimeoutError:
            return self.Result.TIMEOUT
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.error(f"Failed to finish monitoring <{self.name()}>: {ex}")
            return self.Result.ERROR

    @classmethod
    def from_config(cls, name: str, config: Config) -> Self:
        return cls(
            name=name,
            command=config.get_str("command"),
            start_key=config.get_str("start_key"),
            connection_config=ConnectionConfig.from_config(
                config.section("connection")
            ),
            start_timeout=config.get_float("start_timeout"),
            finish_config=FinishConfig.from_config(config.section("finish")),
        )
