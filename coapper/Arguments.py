from pathlib import Path
from typing import Protocol

from .net import Address as Address


class Arguments(Protocol):
    target: Address
    data: list[Path]
    output_prefix: str
    timeout: int
    delay: int
