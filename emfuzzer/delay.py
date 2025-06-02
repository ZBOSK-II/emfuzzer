# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing 'delay' in experiment execution.
"""

import logging
import time
from typing import Self

from .config import Config

logger = logging.getLogger(__name__)


class Delay:
    """
    Class representing single 'delay' in the experiment.
    Forces experiment to wait for a given number of seconds.
    """

    def __init__(self, value: float, *prefix: str):
        self.value = value
        self.prefix = prefix

    def name(self) -> str:
        return ".".join(self.prefix)

    def wait(self) -> None:
        logger.info(f"Waiting on {self.name()} ({self.value}s)")
        time.sleep(self.value)
        logger.info(f"Wait on {self.name()} done")

    @classmethod
    def from_config(cls, *prefix: str, config: Config) -> Self:
        return cls(config.get_float(*prefix), *prefix)
