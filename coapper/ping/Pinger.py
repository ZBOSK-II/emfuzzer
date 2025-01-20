import logging
import subprocess
from enum import StrEnum, auto

logger = logging.getLogger(__name__)


class Pinger:

    class Result(StrEnum):
        ALIVE = auto()
        TIMEOUT = auto()
        ERROR = auto()

    def __init__(self, host: str, count: int, interval: int = 1):
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

    def check_alive(self, timeout: int) -> Result:
        logger.info(f"Checking `{' '.join(self.args)}`")
        try:
            result = subprocess.run(
                self.args,
                timeout=timeout,
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
