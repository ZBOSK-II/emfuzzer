import logging
import subprocess
from enum import StrEnum, auto
from typing import Self

from ..Config import Config

logger = logging.getLogger(__name__)


class Pinger:

    class Result(StrEnum):
        ALIVE = auto()
        TIMEOUT = auto()
        ERROR = auto()

    def __init__(self, host: str, count: int, interval: int, timeout: float):
        self.timeout = timeout
        self.args = [
            "ping",
            "-c",
            str(count),
            "-i",
            str(interval),
            "-w",
            str((count + 1) * interval),
            host,
        ]

    def check_alive(self) -> Result:
        logger.info(f"Checking `{' '.join(self.args)}`")
        try:
            result = subprocess.run(
                self.args,
                timeout=self.timeout,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.TimeoutExpired:
            logger.warn("Ping timedout")
            return self.Result.TIMEOUT

        if result.returncode != 0:
            logger.warn(f"Ping returned {result.returncode}")
            logger.warn(result.stdout)
            return self.Result.ERROR

        logger.info("Target is alive")
        return self.Result.ALIVE

    @classmethod
    def from_config(cls, host: str, config: Config) -> Self:
        return cls(
            host=host,
            count=config.get_int("count"),
            interval=config.get_int("interval"),
            timeout=config.get_float("timeout"),
        )
