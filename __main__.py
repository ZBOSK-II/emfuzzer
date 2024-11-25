import logging
import sys
import time

from .net import Loop


def main():
    logging.basicConfig(level=logging.DEBUG)

    with Loop(None) as loop:  # TODO
        loop.send(("127.0.0.1", 2000), b"aaaaa")
        time.sleep(10)
    return 0


if __name__ == "__main__":
    sys.exit(main())
