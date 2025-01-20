import logging
import os
import queue
import select
import socket
import threading
from binascii import hexlify
from collections.abc import Callable
from types import TracebackType
from typing import Optional, Self, cast

logger = logging.getLogger(__name__)

type Selectable = int | socket.socket


class Loop:
    def __init__(self, validator: Optional[Callable[[str, bytes], None]]):
        self.interrupted = threading.Event()
        self.pipe = os.pipe()
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.thread = threading.Thread(target=self.__loop, name="NetworkLoop")
        self.queue: queue.Queue[tuple[str, bytes]] = queue.Queue()
        self.validator = validator

    def __loop(self) -> None:
        while not self.interrupted.is_set():
            rlist, wlist, xlist = select.select(
                self.__build_rlist(), self.__build_wlist(), self.__build_xlist()
            )
            if self.interrupted.is_set():
                break

            self.__process_rlist(rlist)
            self.__process_wlist(wlist)
            self.__process_xlist(xlist)

    def __build_rlist(self) -> list[Selectable]:
        return [self.udp, self.pipe[0]]

    def __build_wlist(self) -> list[Selectable]:
        if self.queue.empty():
            return []
        return [self.udp]

    def __build_xlist(self) -> list[Selectable]:
        return self.__build_rlist() + self.__build_wlist()

    def __process_rlist(self, rlist: list[Selectable]) -> None:
        for fd in rlist:
            if fd == self.udp:
                data, addr = self.udp.recvfrom(1024)  # TODO
                logger.info(
                    f"Received {len(data)} bytes from {addr}: {hexlify(data).decode('utf-8')}"
                )
                if self.validator:
                    self.validator(addr, data)
            elif fd == self.pipe[0]:
                os.read(self.pipe[0], 1)

    def __process_wlist(self, wlist: list[Selectable]) -> None:
        for fd in wlist:
            try:
                addr, data = self.queue.get_nowait()
            except queue.Empty:
                continue
            logger.info(
                f"Sending {len(data)} bytes to {addr}: {hexlify(data).decode('utf-8')}"
            )
            cast(socket.socket, fd).sendto(data, addr)

    def __process_xlist(self, xlist: list[Selectable]) -> None:
        for fd in xlist:
            logger.error(f"Error state on {fd}")
        # TODO anything else?

    def start(self) -> None:
        logger.info("Starting network thread")
        self.thread.start()

    def stop(self) -> None:
        logger.info("Interrupting network thread")
        self.interrupted.set()
        self.__wake_select()
        self.thread.join()
        self.udp.close()
        logger.info("Network thread stopped")

    def send(self, addr: str, data: bytes) -> None:
        self.queue.put((addr, data))
        self.__wake_select()

    def __wake_select(self) -> None:
        os.write(self.pipe[1], b"x")

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(
        self,
        type_: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.stop()
