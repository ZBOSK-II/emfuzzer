# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module providing subprocess based sub tasks.
"""

import logging
import signal
import subprocess
from dataclasses import dataclass
from signal import Signals
from typing import Optional, Self

from ..config import Config
from ..context import Context
from ..io import IOLoop
from ..io.streams import StreamLogger
from .subtask import BasicSubTask

logger = logging.getLogger(__name__)


@dataclass
class FinishConfig:
    timeout: float
    signal: Optional[Signals]

    @staticmethod
    def _signal_from_name(name: str) -> Optional[Signals]:
        match name:
            case "NONE":
                return None
            case _:
                return Signals[name]

    @classmethod
    def from_config(cls, config: Config) -> Self:
        return cls(
            config.get_float("timeout"),
            cls._signal_from_name(config.get_str("signal")),
        )


class Subprocess(BasicSubTask):

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        name: str,
        args: list[str],
        shell: bool,
        finish_config: FinishConfig,
        io: IOLoop,
        check_exit_code: bool = True,
    ):
        super().__init__(name)

        self.args = args
        self.shell = shell
        self.finish_config = finish_config

        self.io = io

        self.process: Optional[subprocess.Popen[bytes]] = None

        self.check_exit_code = check_exit_code

    def basic_start(self) -> bool:
        try:
            logger.info(f"<{self.name()}>: Starting {self.args}")
            self.process = subprocess.Popen(  # pylint: disable=consider-using-with
                self.args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=False,
                shell=self.shell,
            )
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logger.error(f"<{self.name()}>: Operation error: {ex}")
            return False

        assert self.process.stdout is not None
        assert self.process.stderr is not None
        self.io.register(StreamLogger(f"<{self.name()}> - STDOUT", self.process.stdout))
        self.io.register(StreamLogger(f"<{self.name()}> - STDERR", self.process.stderr))
        return True

    def finish(self) -> BasicSubTask.Result:
        assert self.process is not None
        assert self.process.stdout is not None
        assert self.process.stderr is not None
        assert self.process.stdin is not None

        result = self._finish_process()

        self.process.terminate()
        self.io.close(self.process.stdin)
        self.io.close(self.process.stdout)
        self.io.close(self.process.stderr)

        return result

    def _finish_process(self) -> BasicSubTask.Result:
        assert self.process is not None

        if self.finish_config.signal:
            logger.info(
                f"<{self.name()}>: Sending signal {self.finish_config.signal.name}"
            )
            self.process.send_signal(self.finish_config.signal)

        try:
            self.process.wait(timeout=self.finish_config.timeout)
        except subprocess.TimeoutExpired:
            logger.warning(f"<{self.name()}>: Operation timeout")
            return self.Result.TIMEOUT
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logger.error(f"<{self.name()}>: Operation error: {ex}")
            return self.Result.ERROR

        returncode = self.process.returncode
        if returncode != 0:
            logger.log(
                logging.WARNING if self.check_exit_code else logging.INFO,
                f"<{self.name()}>: Operation returned {returncode}",
            )
            if self.check_exit_code:
                return self.Result.FAILURE

        logger.info(f"<{self.name()}>: Operation finished successfully")
        return self.Result.SUCCESS

    @staticmethod
    def _signal_from_name(name: str) -> Optional[signal.Signals]:
        match name:
            case "NONE":
                return None
            case _:
                return signal.Signals[name]

    @classmethod
    def from_config(cls, name: str, config: Config, context: Context) -> Self:
        return cls(
            name=name,
            args=config.get_str_list("cmd"),
            shell=config.get_bool("shell"),
            finish_config=FinishConfig.from_config(config.section("finish")),
            io=context.worker(IOLoop),
        )
