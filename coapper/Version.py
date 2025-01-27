import subprocess


def __read_version() -> str:
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
