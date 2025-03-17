import logging
import threading
import time
from typing import Callable

import paramiko

logger = logging.getLogger(__name__)

type ParamikoStream = paramiko.ChannelFile[bytes]
type StreamFactory = Callable[[], ParamikoStream]


class Reader:
    def __init__(self, name: str, stdout: StreamFactory, stderr: StreamFactory):
        self.name = name
        self.stdout = stdout
        self.stderr = stderr
        self.kill = threading.Event()
        self.threads: list[threading.Thread] = []

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
        logger.info("Stopping reader threads")

        self.kill.set()

        for thread in self.threads:
            thread.join()

        logger.info("Reader threads stopped")

        self.threads = []

    def __log_stderr(self, line: bytes) -> None:
        logger.warning(f"{self.name} - STDERR: {line!r}")

    def __log_stdout(self, line: bytes) -> None:
        logger.info(f"{self.name} - STDOUT: {line!r}")

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
            else:
                time.sleep(0.01)
