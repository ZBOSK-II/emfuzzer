# Copyright (c) 2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing specific case instance (with id and data).
"""

import logging
from pathlib import Path

from ..arguments import Arguments

logger = logging.getLogger(__name__)


class CaseData:
    def __init__(self, path: Path):
        self._path = path
        self._id = str(path)
        self._contents = bytes()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def identifier(self) -> str:
        return self._id

    @property
    def contents(self) -> bytes:
        if self._contents:
            return self._contents
        logger.info(f"Opening {self._path}")
        with self._path.open("rb") as file:
            self._contents = file.read()
        return self._contents


class CaseInstance:
    def __init__(self, case_id: str, data: CaseData):
        self._id = case_id
        self._data = data

    @property
    def identifier(self) -> str:
        return self._id

    @property
    def data(self) -> CaseData:
        return self._data

    @staticmethod
    def list_from(args: Arguments) -> list[CaseInstance]:
        data = [CaseData(p) for p in args.data]
        return [CaseInstance(d.identifier, d) for d in data]
