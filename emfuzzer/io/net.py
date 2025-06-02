# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Generic Network I/O components.
"""

from dataclasses import dataclass
from typing import Protocol, Self

from ..config import Config


@dataclass
class NetworkAddress:
    host: str
    port: int

    def as_tuple(self) -> tuple[str, int]:
        return self.host, self.port

    @classmethod
    def from_config(cls, config: Config) -> Self:
        return cls(config.get_str("host"), config.get_int("port"))


class NetworkObserver(Protocol):

    def on_read(self, address: NetworkAddress, data: bytes) -> None: ...
    def on_write(self, address: NetworkAddress, data: bytes) -> None: ...
