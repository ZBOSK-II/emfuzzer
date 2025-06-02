# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Stream (files, pipes etc.) bases I/O components.
"""

import logging
from typing import IO

from . import Selectable

logger = logging.getLogger(__name__)


class Stream(Selectable):
    def __init__(self, name: str, stream: IO[bytes]):
        super().__init__(name)
        self.stream = stream

    def close(self) -> None:
        self.stream.close()

    def fileno(self) -> int:
        return self.stream.fileno()

    def is_closed(self) -> bool:
        return self.stream.closed


class InputStream(Stream):
    def write(self) -> None:
        raise RuntimeError("Should be used only for reading")

    def wants_to_write(self) -> bool:
        return False

    def wants_to_read(self) -> bool:
        return True


class OutputStream(Stream):
    def read(self) -> None:
        raise RuntimeError("Should be used only for writing")

    def wants_to_read(self) -> bool:
        return False

    def wants_to_write(self) -> bool:
        return False


class StreamWriter(OutputStream):
    def __init__(self, name: str, stream: IO[bytes], data: bytes):
        super().__init__(name, stream)
        self._data = data

    def write(self) -> None:
        logger.info(f"{self.name()}: writing {len(self._data)} bytes.")

        written = self.stream.write(self._data)
        self._data = self._data[written:]

        logger.info(
            f"{self.name()}: wrote {written}, {len(self._data)} bytes remaining."
        )
        if len(self._data) == 0:
            logger.info(f"{self.name()}: closing the stream")
            self.close()

    def wants_to_write(self) -> bool:
        return len(self._data) > 0


class StreamLogger(InputStream):
    def __init__(self, name: str, stream: IO[bytes]):
        super().__init__(name, stream)

        self._buffer = bytearray()

    def read(self) -> None:
        for b in self.stream.read(1024):
            if b == b"\n"[0]:
                self._flush()
            else:
                self._buffer.append(b)

    def _flush(self) -> None:
        logger.info(f"{self.name()}: {bytes(self._buffer.rstrip())!r}")
        self._buffer.clear()
