import argparse
import logging
import sys
from pathlib import Path

from .Fuzzer import fuzz


def __parse_target(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> tuple[str, int]:
    return args.host, args.port


def __parse_data(parser: argparse.ArgumentParser, data: list[str]) -> list[Path]:
    result = [Path(f) for f in data]
    for f in result:
        if not f.is_file():
            parser.error(f"Specified path is not a file: {f}")
    return result


def parse_args() -> argparse.Namespace:
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

    args = parser.parse_args()

    args.data = __parse_data(parser, args.data)
    args.target = __parse_target(parser, args)

    return args


def main() -> int:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)8s](%(name)20s): %(message)s",
    )

    args = parse_args()

    return fuzz(args.target, args.data, args.timeout, args.delay)


if __name__ == "__main__":
    sys.exit(main())
