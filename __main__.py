import sys
import socket
import logging

from .net import Loop


def main():
    logging.basicConfig(level=logging.DEBUG)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    loop = Loop(sock)  # TODO
    loop.start()
    loop.send(b"aaaaa")
    return 0


if __name__ == "__main__":
    sys.exit(main())
