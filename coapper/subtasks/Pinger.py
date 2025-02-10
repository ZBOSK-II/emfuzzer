from typing import Self

from ..Config import Config
from .Subprocess import Subprocess


class Pinger(Subprocess):

    def __init__(self, name: str, host: str, count: int, interval: int, timeout: float):
        super().__init__(
            name=name,
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
    def from_config(cls, name: str, config: Config) -> Self:
        return cls(
            name=name,
            host=config.get_str("host"),
            count=config.get_int("count"),
            interval=config.get_int("interval"),
            timeout=config.get_float("timeout"),
        )
