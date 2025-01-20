import logging
import subprocess

logger = logging.getLogger(__name__)


class Pinger:

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

        self.total = 0
        self.timedout = 0
        self.failed = 0

    def check_alive(self, timeout: int) -> None:
        self.total += 1

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
            self.timedout += 1
            return

        if result.returncode != 0:
            logger.warn(f"Ping returned {result.returncode}")
            logger.warn(result.stdout)
            self.failed += 1
            return

        logger.info("Target is alive")

    def total_errors(self) -> int:
        return self.timedout + self.failed
