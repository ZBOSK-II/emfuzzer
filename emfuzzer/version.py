# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module providing current version of the application.
"""

import importlib.metadata
import subprocess
from pathlib import Path


def __read_version() -> str:
    version_file = Path(__file__).parent / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()

    try:
        return importlib.metadata.version(__name__.split(".", maxsplit=1)[0])
    except importlib.metadata.PackageNotFoundError:
        pass

    try:
        result = subprocess.run(
            [
                "git",
                "describe",
                "--tags",
                "--dirty",
                "--always",
                "--abbrev=6",
            ],
            timeout=2,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "Unknown"

    if result.returncode != 0:
        return "Unknown"

    return result.stdout.decode("utf-8").strip()


VERSION = __read_version()
