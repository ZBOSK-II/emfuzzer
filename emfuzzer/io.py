# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

import logging
import os
import queue
import select
import threading
from typing import IO

from .context import Worker

logger = logging.getLogger(__name__)


class Stream:
    def __init__(self, name: str, stream: IO[str]):
        self.name = name
        self.stream = stream

        self._buffer = ""

    def read(self) -> None:
        for b in self.stream.read(1024):
            if b == "\n":
                self._flush()
            else:
                self._buffer += b

    def close(self) -> None:
        self.stream.close()

    def fileno(self) -> int:
        return self.stream.fileno()

    def is_closed(self) -> bool:
        return self.stream.closed

    def _flush(self) -> None:
        logger.info(f"{self.name}: {self._buffer.rstrip()}")
        self._buffer = ""


class IOReader(Worker):

    def __init__(self) -> None:
        self._thread = threading.Thread(name="io-reader", target=self._process)
        self._stop_request = threading.Event()
        self._interrupt_pipe = os.pipe()
        self._streams: dict[int, Stream] = {}
        self._register_queue: queue.Queue[Stream] = queue.Queue()
        self._close_queue: queue.Queue[IO[str]] = queue.Queue()

    def start(self) -> None:
        logger.info("Starting subprocess read thread")
        self._thread.start()

    def stop(self) -> None:
        logger.info("Stopping subprocess read thread")
        self._stop_request.set()
        self._wake_select()
        self._thread.join()
        for stream in self._streams.values():
            stream.close()
        logger.info("Stopped subprocess read thread")

    def register(self, name: str, stream: IO[str]) -> None:
        self._register_queue.put(Stream(name, stream))
        self._wake_select()

    def close(self, stream: IO[str]) -> None:
        self._close_queue.put(stream)
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
            stream.fileno() for stream in self._streams.values()
        ]

    def _process_register_queue(self) -> None:
        while not self._register_queue.empty():
            try:
                stream = self._register_queue.get_nowait()
            except queue.Empty:
                return

            self._streams[stream.fileno()] = stream

    def _process_close_queue(self) -> None:
        while not self._close_queue.empty():
            try:
                stream = self._close_queue.get_nowait()
            except queue.Empty:
                return

            stream.close()

    def _clean_closed(self) -> None:
        self._streams = {
            fd: stream for fd, stream in self._streams.items() if not stream.is_closed()
        }

    def _process_rlist(self, rlist: list[int]) -> None:
        for fd in rlist:
            if fd == self._interrupt_pipe[0]:
                os.read(fd, 1)
            else:
                self._process_fd(fd)

    def _process_fd(self, fd: int) -> None:
        stream = self._streams.get(fd)
        if stream is None:
            logger.warning(f"Processing of non-existing fd: {fd}")
            return

        if not stream.is_closed():
            stream.read()
