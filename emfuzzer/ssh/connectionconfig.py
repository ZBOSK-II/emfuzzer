# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module for representing SSH connection configuration.
"""

from dataclasses import dataclass
from typing import Self

from ..config import Config


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
