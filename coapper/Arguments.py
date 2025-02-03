from pathlib import Path
from typing import Protocol


class Arguments(Protocol):
    data: list[Path]
    output_prefix: str
    config: Path
