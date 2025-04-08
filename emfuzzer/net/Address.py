# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

from dataclasses import dataclass
from typing import Self

from ..Config import Config


@dataclass
class Address:
    host: str
    port: int

    def as_tuple(self) -> tuple[str, int]:
        return self.host, self.port

    @classmethod
    def from_config(cls, config: Config) -> Self:
        return cls(config.get_str("host"), config.get_int("port"))
