# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

from pathlib import Path
from typing import Protocol


class Arguments(Protocol):
    data: list[Path]
    output_prefix: str
    config: Path
