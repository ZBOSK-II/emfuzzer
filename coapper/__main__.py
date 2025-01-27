import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from .Arguments import Address, Arguments
from .Fuzzer import fuzz
from .Version import VERSION


def __parse_target(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> Address:
    return Address(args.host, args.port)


def __parse_data(parser: argparse.ArgumentParser, data: list[str]) -> list[Path]:
    result = [Path(f) for f in data]
    for f in result:
        if not f.is_file():
            parser.error(f"Specified path is not a file: {f}")
    return result


def __setup_logger(prefix: str):
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
        prog="CoAP Fuzzer", description="Fuzzes CoAP target using provided data"
    )
    parser.add_argument(
        "data",
        nargs="+",
        help="List of files containing binary data to send to the target",
    )
    parser.add_argument(
        "--host",
        help="Target of the packets",
        default="127.0.0.1",
    )
    parser.add_argument(
        "--port",
        help="Target port of the packets",
        default=5683,
        type=int,
    )
    parser.add_argument(
        "--timeout",
        help="Timeout to be used for each operation",
        default=5,
        type=float,
    )
    parser.add_argument(
        "--delay",
        help="Delay between operations",
        default=0.2,
        type=float,
    )
    parser.add_argument(
        "--output-prefix",
        help="Prefix to be used for saving output (logs, reports, etc.)",
        default="coapper",
        type=str,
    )

    args = parser.parse_args()

    args.data = __parse_data(parser, args.data)
    args.target = __parse_target(parser, args)
    args.output_prefix += f"-{datetime.now():%Y%m%d-%H%M%S}"

    return args


def main() -> int:
    args = parse_args()

    __setup_logger(args.output_prefix)

    return fuzz(args)


if __name__ == "__main__":
    sys.exit(main())
