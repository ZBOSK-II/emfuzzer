import subprocess
from pathlib import Path


def __read_version() -> str:
    version_file = Path(__file__).parent / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()

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
        )
    except subprocess.TimeoutExpired:
        return "Unknown"

    if result.returncode != 0:
        return "Unknown"

    return result.stdout.decode("utf-8").strip()


VERSION = __read_version()
