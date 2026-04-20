# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Main entry point to the application.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from . import run
from .arguments import Arguments, RepeatMode
from .config import Config
from .version import VERSION


def __parse_data(parser: argparse.ArgumentParser, data: list[str]) -> list[Path]:
    result = [Path(f) for f in data]
    for f in result:
        if not f.is_file():
            parser.error(f"Specified path is not a file: {f}")
    if len(result) != len(set(result)):
        parser.error("Non-unique file names as inputs - results would be inconsistent")
    return result


def __setup_logger(prefix: str) -> None:
    log_format = "%(asctime)s [%(levelname)8s](%(name)20s): %(message)s"
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
    )

    root_logger = logging.getLogger()
    handler = logging.FileHandler(f"{prefix}.log")
    handler.setFormatter(root_logger.handlers[0].formatter)
    logging.getLogger().addHandler(handler)

    root_logger.info(f"Started instance ({VERSION})")


def parse_args() -> Arguments:
    parser = argparse.ArgumentParser(
        prog="emtorch",
        description="Experiments orchestrator for embedded systems",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "data",
        nargs="+",
        help="list of files containing binary data to send to the target",
    )
    parser.add_argument(
        "--output-prefix",
        help="prefix to be used for saving output (logs, reports, etc.)",
        default="emtorch",
        type=str,
    )
    parser.add_argument(
        "--config",
        help="path to the configuration file",
        default="default-config.json",
        type=Path,
    )
    parser.add_argument(
        "--repeats",
        help="number of times to repeat each data file",
        default=1,
        type=int,
    )
    parser.add_argument(
        "--repeat-mode",
        help="pattern used when repeating ('aabb' or 'abab')",
        choices=("aabb", "abab"),
        default="aabb",
        type=str,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=VERSION,
    )

    args = parser.parse_args()

    if args.repeats < 1:
        parser.error("--repeats must be >= 1")

    args.data = __parse_data(parser, args.data)
    args.repeat_mode = RepeatMode(args.repeat_mode)
    args.output_prefix += f"-{datetime.now():%Y%m%d-%H%M%S}"

    return Arguments(**vars(args))


def main() -> int:
    args = parse_args()

    __setup_logger(args.output_prefix)

    return run(args, Config.from_file(args.config))


if __name__ == "__main__":
    sys.exit(main())
