# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

import logging
import socket
from binascii import hexlify

from . import Selectable

logger = logging.getLogger(__name__)


class Socket(Selectable):
    def __init__(self, name: str, sock: socket.socket):
        super().__init__(name)
        self.socket = sock
        self._closed = False

    def close(self) -> None:
        self.socket.close()
        self._closed = True

    def fileno(self) -> int:
        return self.socket.fileno()

    def is_closed(self) -> bool:
        return self._closed


class UdpClientSocket(Socket):
    def __init__(self, name: str):
        super().__init__(name, socket.socket(socket.AF_INET, socket.SOCK_DGRAM))

    def read(self) -> None:
        data, addr = self.socket.recvfrom(1024)  # TODO pylint: disable=fixme
        logger.info(
            f"Received {len(data)} bytes from {addr}: {hexlify(data).decode('utf-8')}"
        )
