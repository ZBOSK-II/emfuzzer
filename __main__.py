import argparse
import logging
import sys
import time

from pathlib import Path

from .coapp import Validator
from .net import Loop


def __parse_target(parser, args):
    return args.host, args.port


def __parse_data(parser, data):
    data = [Path(f) for f in data]
    for f in data:
        if not f.is_file():
            parser.error(f"Specified path is not a file: {f}")
    return data


def parse_args():
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
    # TODO delay
    # TODO timeout
    args = parser.parse_args()

    args.data = __parse_data(parser, args.data)
    args.target = __parse_target(parser, args)

    return args


def main():
    logging.basicConfig(level=logging.DEBUG)

    args = parse_args()

    validator = Validator(args.target)

    with Loop(validator) as loop:  # TODO
        loop.send(args.target, b"aaaaa")
        validator.wait_for_validation()
    return 0


if __name__ == "__main__":
    sys.exit(main())
