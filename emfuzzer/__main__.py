# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from .arguments import Arguments
from .config import Config
from .fuzzer import fuzz
from .version import VERSION


def __parse_data(parser: argparse.ArgumentParser, data: list[str]) -> list[Path]:
    result = [Path(f) for f in data]
    for f in result:
        if not f.is_file():
            parser.error(f"Specified path is not a file: {f}")
    return result


def __setup_logger(prefix: str) -> None:
    format = "%(asctime)s [%(levelname)8s](%(name)20s): %(message)s"
    logging.basicConfig(
        level=logging.DEBUG,
        format=format,
    )

    root_logger = logging.getLogger()
    handler = logging.FileHandler(f"{prefix}.log")
    handler.setFormatter(root_logger.handlers[0].formatter)
    logging.getLogger().addHandler(handler)

    root_logger.info(f"Started instance ({VERSION})")


def parse_args() -> Arguments:
    parser = argparse.ArgumentParser(
        prog="emfuzzer",
        description="Fuzzer for embedded applications (with CoAP support)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "data",
        nargs="+",
        help="List of files containing binary data to send to the target",
    )
    parser.add_argument(
        "--output-prefix",
        help="Prefix to be used for saving output (logs, reports, etc.)",
        default="emfuzzer",
        type=str,
    )
    parser.add_argument(
        "--config",
        help="Path to the configuration file",
        default="default-config.json",
        type=Path,
    )

    args = parser.parse_args()

    args.data = __parse_data(parser, args.data)
    args.output_prefix += f"-{datetime.now():%Y%m%d-%H%M%S}"

    return args


def main() -> int:
    args = parse_args()

    __setup_logger(args.output_prefix)

    return fuzz(args, Config.from_file(args.config))


if __name__ == "__main__":
    sys.exit(main())
