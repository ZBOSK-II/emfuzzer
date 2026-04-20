# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing command line arguments.
"""

from enum import Enum
from pathlib import Path
from typing import Protocol


class RepeatMode(Enum):
    AABB = "aabb"
    ABAB = "abab"


class Arguments(Protocol):  # pylint: disable=too-few-public-methods
    data: list[Path]
    output_prefix: str
    config: Path
    repeats: int
    repeat_mode: RepeatMode
