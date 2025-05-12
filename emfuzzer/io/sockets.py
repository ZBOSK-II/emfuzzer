# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

import logging
import socket
from binascii import hexlify

from . import Selectable, SendQueue
from .net import NetworkAddress

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
    def __init__(self, name: str, queue: SendQueue[tuple[NetworkAddress, bytes]]):
        super().__init__(name, socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
        self._queue = queue

    def read(self) -> None:
        data, addr = self.socket.recvfrom(1024)  # TODO pylint: disable=fixme
        logger.info(
            f"Received {len(data)} bytes from {addr}: {hexlify(data).decode('utf-8')}"
        )
        # consumer . on_read

    def wants_to_write(self) -> bool:
        return not self._queue.empty()

    def write(self) -> None:
        try:
            addr, data = self._queue.get()
        except SendQueue.Empty:
            return
        logger.info(
            f"Sending {len(data)} bytes to {addr}: {hexlify(data).decode('utf-8')}"
        )
        # consumer . on_send
        self.socket.sendto(data, addr.as_tuple())
