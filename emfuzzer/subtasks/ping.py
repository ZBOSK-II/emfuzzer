# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module holding sub-tasks related to network "ping".
"""

import logging
import subprocess
from typing import IO, Self

from ..config import Config
from ..context import Context
from ..io import IOLoop
from ..io.streams import InputStream
from .subprocess import FinishConfig, Subprocess

logger = logging.getLogger(__name__)


class PingIsAliveStream(InputStream):
    def __init__(self, name: str, stream: IO[bytes], process: subprocess.Popen[bytes]):
        super().__init__(name, stream)

        self.header = b""
        self.header_done = False
        self.response_received = False

        self.process = process

    def read(self) -> None:
        char = self.stream.read(1)
        if self.header_done:
            match char:
                case b"\b":
                    if not self.response_received:
                        logger.info(f"<{self.name()}>: Response received")
                    self.response_received = True
                case b".":
                    if self.response_received:
                        logger.info(f"<{self.name()}>: Ping received")
                        # if process finishes before external timeout - it will be a success
                        self.process.terminate()
                    else:
                        logger.info(f"<{self.name()}>: Ping")
                case b"E":
                    logger.warning(f"<{self.name()}>: error response")
                    self.response_received = False
        else:
            if char == b"\n":
                logger.info(f"<{self.name()}>: {self.header!r}")
                self.header_done = True
            else:
                self.header += char


class PingIsAlive(Subprocess):
    """
    Waits for first ping response (up to timeout).
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, name: str, host: str, interval: int, timeout: float, io: IOLoop):

        super().__init__(
            name=name,
            finish_config=FinishConfig(timeout, None),
            args=[
                "ping",
                "-f",
                "-i",
                str(interval),
                host,
            ],
            shell=False,
            io=io,
            check_exit_code=False,
        )

        self.stream: PingIsAliveStream | None = None

    def basic_start(self) -> bool:
        if not super().basic_start():
            return False

        assert self.process is not None
        assert self.process.stdout is not None

        self.stream = PingIsAliveStream(self.name(), self.process.stdout, self.process)
        self.io.register(self.stream)  # overrides registration done by parent

        return True

    def finish(self) -> Subprocess.Result:
        if super().finish() == Subprocess.Result.ERROR:
            return Subprocess.Result.ERROR
        assert self.stream is not None
        return (
            Subprocess.Result.SUCCESS
            if self.stream.response_received
            else Subprocess.Result.FAILURE
        )

    @classmethod
    def from_config(cls, name: str, config: Config, context: Context) -> Self:
        return cls(
            name=name,
            host=config.get_str("host"),
            timeout=config.get_float("timeout"),
            interval=config.get_int("interval"),
            io=context.worker(IOLoop),
        )


class PingIsStable(Subprocess):
    """
    Executes `count` pings and expects replies from all of them.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, name: str, host: str, count: int, interval: int, io: IOLoop):
        timeout = (count + 1) * interval
        super().__init__(
            name=name,
            finish_config=FinishConfig(timeout, None),
            args=[
                "ping",
                "-c",
                str(count),
                "-i",
                str(interval),
                "-w",
                str(timeout),
                host,
            ],
            shell=False,
            io=io,
        )

    @classmethod
    def from_config(cls, name: str, config: Config, context: Context) -> Self:
        return cls(
            name=name,
            host=config.get_str("host"),
            count=config.get_int("count"),
            interval=config.get_int("interval"),
            io=context.worker(IOLoop),
        )
