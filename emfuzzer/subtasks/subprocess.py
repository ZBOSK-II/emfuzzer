# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

import logging
import os
import queue
import select
import signal
import subprocess
import threading
from dataclasses import dataclass
from signal import Signals
from typing import IO, Optional, Self

from ..config import Config
from ..context import Context, Worker
from .runnable import Runnable

logger = logging.getLogger(__name__)


@dataclass
class FinishConfig:
    timeout: float
    signal: Optional[Signals]

    @staticmethod
    def _signal_from_name(name: str) -> Optional[Signals]:
        match name:
            case "NONE":
                return None
            case _:
                return Signals[name]

    @classmethod
    def from_config(cls, config: Config) -> Self:
        return cls(
            config.get_float("timeout"),
            cls._signal_from_name(config.get_str("signal")),
        )


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


class Reader(Worker):

    def __init__(self) -> None:
        self._thread = threading.Thread(name="subprocess-reader", target=self._process)
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


class Subprocess(Runnable):

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        name: str,
        args: list[str],
        shell: bool,
        finish_config: FinishConfig,
        reader: Reader,
    ):
        super().__init__(name)

        self.args = args
        self.shell = shell
        self.finish_config = finish_config

        self.reader = reader

        self.process: Optional[subprocess.Popen[str]] = None

    def start(self) -> bool:
        try:
            logger.info(f"<{self.name()}>: Starting {self.args}")
            self.process = subprocess.Popen(  # pylint: disable=consider-using-with
                self.args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=self.shell,
            )
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logger.error(f"<{self.name()}>: Operation error: {ex}")
            return False

        assert self.process.stdout is not None
        assert self.process.stderr is not None
        self.reader.register(f"<{self.name()}> - STDOUT", self.process.stdout)
        self.reader.register(f"<{self.name()}> - STDERR", self.process.stderr)
        return True

    def finish(self) -> Runnable.Result:
        assert self.process is not None
        assert self.process.stdout is not None
        assert self.process.stderr is not None

        result = self._finish_process()

        self.process.terminate()
        self.reader.close(self.process.stdout)
        self.reader.close(self.process.stderr)

        return result

    def _finish_process(self) -> Runnable.Result:
        assert self.process is not None

        if self.finish_config.signal:
            logger.info(
                f"<{self.name()}>: Sending signal {self.finish_config.signal.name}"
            )
            self.process.send_signal(self.finish_config.signal)

        try:
            self.process.wait(timeout=self.finish_config.timeout)
        except subprocess.TimeoutExpired:
            logger.warning(f"<{self.name()}>: Operation timeout")
            return self.Result.TIMEOUT
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logger.error(f"<{self.name()}>: Operation error: {ex}")
            return self.Result.ERROR

        returncode = self.process.returncode
        if returncode != 0:
            logger.warning(f"<{self.name()}>: Operation returned {returncode}")
            return self.Result.FAILURE

        logger.info(f"<{self.name()}>: Operation finished successfully")
        return self.Result.SUCCESS

    @staticmethod
    def _signal_from_name(name: str) -> Optional[signal.Signals]:
        match name:
            case "NONE":
                return None
            case _:
                return signal.Signals[name]

    @classmethod
    def from_config(cls, name: str, config: Config, context: Context) -> Self:
        return cls(
            name=name,
            args=config.get_str_list("cmd"),
            shell=config.get_bool("shell"),
            finish_config=FinishConfig.from_config(config.section("finish")),
            reader=context.worker(Reader),
        )
