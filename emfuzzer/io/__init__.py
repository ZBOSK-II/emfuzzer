# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
I/O handling components.
"""

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
    def close(self) -> None: ...

    @abstractmethod
    def is_closed(self) -> bool: ...

    @abstractmethod
    def wants_to_read(self) -> bool: ...

    @abstractmethod
    def read(self) -> None: ...

    @abstractmethod
    def wants_to_write(self) -> bool: ...

    @abstractmethod
    def write(self) -> None: ...


class InterruptPipe(Selectable):
    def __init__(self) -> None:
        super().__init__("interrupt-pipe")
        self._pipe = os.pipe()

    def fileno(self) -> int:
        return self._pipe[0]

    def write(self) -> None:
        os.write(self._pipe[1], b"x")

    def read(self) -> None:
        os.read(self.fileno(), 1024)

    def close(self) -> None:
        # should be called only when closing IOLoop
        os.close(self._pipe[0])
        os.close(self._pipe[1])

    def is_closed(self) -> bool:
        # never during IOLoop operations
        return False

    def wants_to_write(self) -> bool:
        # it should never write through "selection"
        return False

    def wants_to_read(self) -> bool:
        return True


class SendQueue[T](ABC):
    Empty: type[Exception] = queue.Empty

    def __init__(self) -> None:
        self._queue: queue.Queue[T] = queue.Queue()

    @abstractmethod
    def put(self, element: T) -> None: ...

    def get(self) -> T:
        return self._queue.get_nowait()

    def empty(self) -> bool:
        return self._queue.empty()


class IOLoop(Worker):

    def __init__(self) -> None:
        self._thread = threading.Thread(name="io-reader", target=self._process)
        self._stop_request = threading.Event()
        self._interrupt_pipe = InterruptPipe()
        self._selectables: dict[int, Selectable] = {}
        self._register_queue: queue.Queue[Selectable] = queue.Queue()
        self._close_queue: queue.Queue[Closeable] = queue.Queue()

        self._perform_register(self._interrupt_pipe)

    def start(self) -> None:
        logger.info("Starting I/O thread")
        self._thread.start()

    def stop(self) -> None:
        logger.info("Stopping I/O thread")
        self._stop_request.set()
        self._wake_select()
        self._thread.join()
        for selectable in self._selectables.values():
            selectable.close()
        logger.info("Stopped subprocess read thread")

    def register(self, selectable: Selectable) -> None:
        self._register_queue.put(selectable)
        self._wake_select()

    # pylint: disable=unused-argument
    def make_queue[T](self, send_type: type[T]) -> SendQueue[T]:
        parent = self

        class Queue(SendQueue[T]):
            def put(self, element: T) -> None:
                self._queue.put(element)
                # pylint: disable=protected-access
                parent._wake_select()

        return Queue()

    def close(self, closeable: Closeable) -> None:
        self._close_queue.put(closeable)
        self._wake_select()

    def _process(self) -> None:
        while not self._stop_request.is_set():
            rlist, wlist, _ = select.select(
                self._build_rlist(), self._build_wlist(), []
            )

            if self._stop_request.is_set():
                return

            self._process_rlist(rlist)
            self._process_wlist(wlist)
            self._process_register_queue()
            self._process_close_queue()
            self._clean_closed()

    def _wake_select(self) -> None:
        self._interrupt_pipe.write()

    def _build_rlist(self) -> list[int]:
        return [
            selectable.fileno()
            for selectable in self._selectables.values()
            if selectable.wants_to_read()
        ]

    def _build_wlist(self) -> list[int]:
        return [
            selectable.fileno()
            for selectable in self._selectables.values()
            if selectable.wants_to_write()
        ]

    def _perform_register(self, selectable: Selectable) -> None:
        self._selectables[selectable.fileno()] = selectable

    def _process_register_queue(self) -> None:
        while not self._register_queue.empty():
            try:
                self._perform_register(self._register_queue.get_nowait())
            except queue.Empty:
                return

    def _process_close_queue(self) -> None:
        while not self._close_queue.empty():
            try:
                closeable = self._close_queue.get_nowait()
            except queue.Empty:
                return

            try:
                closeable.close()
            except IOError as ex:
                logger.error(f"Error during closing {ex}, {closeable}")

    def _clean_closed(self) -> None:
        self._selectables = {
            fd: selectable
            for fd, selectable in self._selectables.items()
            if not selectable.is_closed()
        }

    def _process_rlist(self, rlist: list[int]) -> None:
        for fd in rlist:
            selectable = self._selectables.get(fd)
            if selectable is None:
                logger.warning(f"Processing reading of non-existing fd: {fd}")
                return

            if not selectable.is_closed():
                selectable.read()

    def _process_wlist(self, wlist: list[int]) -> None:
        for fd in wlist:
            selectable = self._selectables.get(fd)
            if selectable is None:
                logger.warning(f"Processing writing of non-existing fd: {fd}")
                return

            if not selectable.is_closed():
                selectable.write()
