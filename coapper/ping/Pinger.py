from typing import Self

from ..Config import Config
from ..subtasks.Subprocess import Subprocess


class Pinger(Subprocess):

    def __init__(self, host: str, count: int, interval: int, timeout: float):
        super().__init__(
            name="Pinger",
            timeout=timeout,
            args=[
                "ping",
                "-c",
                str(count),
                "-i",
                str(interval),
                "-w",
                str((count + 1) * interval),
                host,
            ],
            shell=False,
        )

    def check_alive(self) -> Subprocess.Result:
        return self.run()

    @classmethod
    def from_config(cls, host: str, config: Config) -> Self:
        return cls(
            host=host,
            count=config.get_int("count"),
            interval=config.get_int("interval"),
            timeout=config.get_float("timeout"),
        )
