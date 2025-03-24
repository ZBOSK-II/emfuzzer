from dataclasses import dataclass
from typing import Self

from ..Config import Config


@dataclass
class ConnectionConfig:
    host: str
    port: int
    username: str
    password: str

    @classmethod
    def from_config(cls, config: Config) -> Self:
        return cls(
            config.get_str("host"),
            config.get_int("port"),
            config.get_str("username"),
            config.get_str("password"),
        )
