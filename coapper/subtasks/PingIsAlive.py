import logging
import select
import subprocess
import time
from typing import Self

from ..Config import Config
from . import Runnable

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
            text=True,
            bufsize=1,
        ) as process:
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                rlist, _, xlist = select.select(
                    [process.stdout],
                    [],
                    [process.stdout],
                    self.timeout - (time.time() - start_time),
                )
                if xlist:
                    logger.warn(f"<{self.name()}>: Read failure")
                    process.terminate()
                    return self.Result.FAILURE
                if rlist:
                    match rlist[0].read(1):
                        case "\b":
                            logger.info(f"<{self.name()}>: Response received")
                            process.terminate()
                            return self.Result.SUCCESS
                        case ".":
                            logger.info(f"<{self.name()}>: Ping")

            logger.warn(f"<{self.name()}>: Ping failure!")
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
