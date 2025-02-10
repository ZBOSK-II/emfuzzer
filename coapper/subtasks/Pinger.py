from typing import Self

from ..Config import Config
from .Subprocess import Subprocess


class Pinger(Subprocess):
    """
    Executes `count` pings and expects replies from all of them.
    """

    def __init__(self, name: str, host: str, count: int, interval: int):
        timeout = (count + 1) * interval
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
                str(timeout),
                host,
            ],
            shell=False,
        )

    @classmethod
    def from_config(cls, name: str, config: Config) -> Self:
        return cls(
            name=name,
            host=config.get_str("host"),
            count=config.get_int("count"),
            interval=config.get_int("interval"),
        )
