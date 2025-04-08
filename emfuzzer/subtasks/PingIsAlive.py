# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

import logging
import select
import subprocess
import time
from typing import Self

from ..Config import Config
from .Runnable import Runnable

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

    def run(self) -> Runnable.Result:
        logger.info(f"<{self.name()}>: Checking is alive via ping")
        with subprocess.Popen(
            ["ping", "-f", "-i", str(self.interval), self.host],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as process:
            start_time = time.time()
            header = b""
            header_done = False
            response_received = False
            while (elapsed_time := time.time() - start_time) < self.timeout:
                rlist, _, xlist = select.select(
                    [process.stdout],
                    [],
                    [process.stdout],
                    self.timeout - elapsed_time,
                )
                if xlist:
                    logger.warn(f"<{self.name()}>: Read failure")
                    process.terminate()
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
                                    process.terminate()
                                    return self.Result.SUCCESS
                                else:
                                    logger.info(f"<{self.name()}>: Ping")
                            case b"E":
                                logger.warn(f"<{self.name()}>: error response")
                                response_received = False
                    else:
                        if char == b"\n":
                            logger.info(f"<{self.name()}>: {header!r}")
                            header_done = True
                        else:
                            header += char

            logger.warn(f"<{self.name()}>: Ping timeout!")
            process.terminate()
            return self.Result.TIMEOUT

    @classmethod
    def from_config(cls, name: str, config: Config) -> Self:
        return cls(
            name=name,
            host=config.get_str("host"),
            timeout=config.get_float("timeout"),
            interval=config.get_int("interval"),
        )
