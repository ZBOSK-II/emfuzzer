# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

import logging
import os
import queue
import select
import threading
from abc import ABC, abstractmethod
from typing import Protocol

from ..context import Worker

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class Closeable(Protocol):
    def close(self) -> None: ...


class Selectable(ABC):
    def __init__(self, name: str):
        self._name = name

    def name(self) -> str:
        return self._name

    @abstractmethod
    def fileno(self) -> int: ...

    @abstractmethod
    def read(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def is_closed(self) -> bool: ...


class IOLoop(Worker):

    def __init__(self) -> None:
        self._thread = threading.Thread(name="io-reader", target=self._process)
        self._stop_request = threading.Event()
        self._interrupt_pipe = os.pipe()
        self._selectables: dict[int, Selectable] = {}
        self._register_queue: queue.Queue[Selectable] = queue.Queue()
        self._close_queue: queue.Queue[Closeable] = queue.Queue()

    def start(self) -> None:
        logger.info("Starting subprocess read thread")
        self._thread.start()

    def stop(self) -> None:
        logger.info("Stopping subprocess read thread")
        self._stop_request.set()
        self._wake_select()
        self._thread.join()
        for selectable in self._selectables.values():
            selectable.close()
        logger.info("Stopped subprocess read thread")

    def register(self, selectable: Selectable) -> None:
        self._register_queue.put(selectable)
        self._wake_select()

    def close(self, closeable: Closeable) -> None:
        self._close_queue.put(closeable)
        self._wake_select()

    def _process(self) -> None:
        while not self._stop_request.is_set():
            rlist, _, _ = select.select(self._build_rlist(), [], [])

            if self._stop_request.is_set():
                return

            self._process_rlist(rlist)
            self._process_register_queue()
            self._process_close_queue()
            self._clean_closed()

    def _wake_select(self) -> None:
        os.write(self._interrupt_pipe[1], b"x")

    def _build_rlist(self) -> list[int]:
        return [self._interrupt_pipe[0]] + [
            selectable.fileno() for selectable in self._selectables.values()
        ]

    def _process_register_queue(self) -> None:
        while not self._register_queue.empty():
            try:
                selectable = self._register_queue.get_nowait()
            except queue.Empty:
                return

            self._selectables[selectable.fileno()] = selectable

    def _process_close_queue(self) -> None:
        while not self._close_queue.empty():
            try:
                closeable = self._close_queue.get_nowait()
            except queue.Empty:
                return

            closeable.close()

    def _clean_closed(self) -> None:
        self._selectables = {
            fd: selectable
            for fd, selectable in self._selectables.items()
            if not selectable.is_closed()
        }

    def _process_rlist(self, rlist: list[int]) -> None:
        for fd in rlist:
            if fd == self._interrupt_pipe[0]:
                os.read(fd, 1)
            else:
                self._process_fd(fd)

    def _process_fd(self, fd: int) -> None:
        selectable = self._selectables.get(fd)
        if selectable is None:
            logger.warning(f"Processing of non-existing fd: {fd}")
            return

        if not selectable.is_closed():
            selectable.read()
