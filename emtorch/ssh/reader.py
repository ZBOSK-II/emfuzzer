# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
SSH connection reader.
"""

import logging
import threading
import time
from typing import Callable

import paramiko

# pylint: disable=unsubscriptable-object
type ParamikoStream = paramiko.ChannelFile[bytes]
type StreamFactory = Callable[[], ParamikoStream]


# pylint: disable=too-many-instance-attributes
class Reader:
    def __init__(
        self, name: str, start_key: str, stdout: StreamFactory, stderr: StreamFactory
    ):
        self.name = name
        self.stdout = stdout
        self.stderr = stderr
        self.kill = threading.Event()
        self.threads: list[threading.Thread] = []
        self.started_event = threading.Event()
        self.start_key = start_key
        self.logger = logging.LoggerAdapter(
            logging.getLogger(__name__), extra={"subtask": name}
        )

    def start(self) -> None:
        # one stream per thread - ugly, but Paramiko does not properly support 'select'...
        self.threads = [
            threading.Thread(
                name="stderr",
                target=self.__read,
                kwargs={
                    "stream": self.stderr(),
                    "line_handler": self.__log_stderr,
                },
            ),
            threading.Thread(
                name="stdout",
                target=self.__read,
                kwargs={
                    "stream": self.stdout(),
                    "line_handler": self.__log_stdout,
                },
            ),
        ]

        self.kill.clear()

        for thread in self.threads:
            thread.start()

    def stop(self) -> None:
        self.logger.info("Stopping reader threads")

        self.kill.set()

        for thread in self.threads:
            thread.join()

        self.logger.info("Reader threads stopped")

        self.threads = []

    def __log_stderr(self, line: bytes) -> None:
        self.logger.warning(f"STDERR - {line!r}")

    def __log_stdout(self, line: bytes) -> None:
        self.logger.info(f"STDOUT - {line!r}")

    def __read(
        self, stream: ParamikoStream, line_handler: Callable[[bytes], None]
    ) -> None:
        while not self.kill.is_set():
            try:
                line = stream.readline()
            except ValueError:
                continue
            if line:
                line_handler(line.rstrip())
                if not self.started_event.is_set() and line.startswith(self.start_key):
                    self.logger.info("start key detected, marking as started")
                    self.started_event.set()
            else:
                time.sleep(0.01)
