import logging
import sys
import time

from .coapp import Validator
from .net import Loop


def main():
    logging.basicConfig(level=logging.DEBUG)

    addr = ("127.0.0.1", 2000)  # TODO
    validator = Validator(addr)

    with Loop(validator) as loop:  # TODO
        loop.send(addr, b"aaaaa")
        validator.wait_for_validation()
    return 0


if __name__ == "__main__":
    sys.exit(main())
