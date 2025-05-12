# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

import logging
import select
import subprocess
import time
from typing import Optional, Self

from ..config import Config
from ..context import Context
from ..io import IOReader
from .runnable import Runnable
from .subprocess import FinishConfig, Subprocess

logger = logging.getLogger(__name__)


class PingIsAlive(Runnable):
    """
    Waits for first ping response (up to timeout).
    """

    def __init__(self, name: str, host: str, interval: int, timeout: float):
        super().__init__(name)

        self.host = host
        self.timeout = timeout
        self.interval = interval
        self.process: Optional[subprocess.Popen[bytes]] = None

    def start(self) -> bool:
        try:
            logger.info(f"<{self.name()}>: Starting ping alive check")
            self.process = subprocess.Popen(  # pylint: disable=consider-using-with
                ["ping", "-f", "-i", str(self.interval), self.host],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logger.error(f"<{self.name()}>: Operation error: {ex}")
            return False

        assert self.process.stdout is not None
        assert self.process.stderr is not None

        return True

    def finish(self) -> Runnable.Result:
        assert self.process is not None
        assert self.process.stdout is not None
        assert self.process.stderr is not None

        start_time = time.time()
        header = b""
        header_done = False
        response_received = False
        while (elapsed_time := time.time() - start_time) < self.timeout:
            rlist, _, xlist = select.select(
                [self.process.stdout],
                [],
                [self.process.stdout],
                self.timeout - elapsed_time,
            )
            if xlist:
                logger.warning(f"<{self.name()}>: Read failure")
                self.process.terminate()
                return self.Result.FAILURE
            if rlist:
                char = rlist[0].read(1)
                if header_done:
                    match char:
                        case b"\b":
                            if not response_received:
                                logger.info(f"<{self.name()}>: Response received")
                            response_received = True
                        case b".":
                            if response_received:
                                logger.info(f"<{self.name()}>: Ping received")
                                self.process.terminate()
                                return self.Result.SUCCESS
                            logger.info(f"<{self.name()}>: Ping")
                        case b"E":
                            logger.warning(f"<{self.name()}>: error response")
                            response_received = False
                else:
                    if char == b"\n":
                        logger.info(f"<{self.name()}>: {header!r}")
                        header_done = True
                    else:
                        header += char

        logger.warning(f"<{self.name()}>: Ping timeout!")
        self.process.terminate()
        return self.Result.TIMEOUT

    @classmethod
    def from_config(cls, name: str, config: Config) -> Self:
        return cls(
            name=name,
            host=config.get_str("host"),
            timeout=config.get_float("timeout"),
            interval=config.get_int("interval"),
        )


class PingIsStable(Subprocess):
    """
    Executes `count` pings and expects replies from all of them.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self, name: str, host: str, count: int, interval: int, reader: IOReader
    ):
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
            reader=reader,
        )

    @classmethod
    def from_config(cls, name: str, config: Config, context: Context) -> Self:
        return cls(
            name=name,
            host=config.get_str("host"),
            count=config.get_int("count"),
            interval=config.get_int("interval"),
            reader=context.worker(IOReader),
        )
