# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

import logging
import subprocess
from typing import Self

from ..config import Config
from .runnable import Runnable

logger = logging.getLogger(__name__)


class Subprocess(Runnable):
    def __init__(
        self,
        args: list[str],
        timeout: float,
        shell: bool = False,
        name: str = "subprocess",
    ):
        super().__init__(name)

        self.args = args
        self.timeout = timeout
        self.shell = shell

    def run(self) -> Runnable.Result:
        logger.info(f"<{self.name()}>: Calling `{' '.join(self.args)}`")
        try:
            result = subprocess.run(
                self.args,
                timeout=self.timeout,
                shell=self.shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.TimeoutExpired:
            logger.warn(f"<{self.name()}: Operation timeout")
            return self.Result.TIMEOUT
        except Exception as ex:
            logger.error(f"<{self.name()}>: Operation error: {ex}")
            return self.Result.ERROR

        if result.returncode != 0:
            logger.warn(f"<{self.name()}>: STDOUT: {result.stdout!r}")
            logger.warn(f"<{self.name()}>: Operation returned {result.returncode}")
            return self.Result.FAILURE

        logger.info(f"<{self.name()}>: STDOUT: {result.stdout!r}")
        logger.info(f"<{self.name()}>: Operation finished successfully")
        return self.Result.SUCCESS

    @classmethod
    def from_config(cls, name: str, config: Config) -> Self:
        return cls(
            name=name,
            args=config.get_str_list("cmd"),
            timeout=config.get_float("timeout"),
            shell=config.get_bool("shell"),
        )
