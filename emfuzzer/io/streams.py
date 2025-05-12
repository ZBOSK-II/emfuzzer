# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

import logging
from typing import IO

from . import Selectable

logger = logging.getLogger(__name__)


class InputStream(Selectable):
    def __init__(self, name: str, stream: IO[bytes]):
        super().__init__(name)
        self.stream = stream

    def close(self) -> None:
        self.stream.close()

    def fileno(self) -> int:
        return self.stream.fileno()

    def is_closed(self) -> bool:
        return self.stream.closed


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
