# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Module representing basic results of the single sub-task.
"""

from enum import StrEnum, auto


class BasicResult(StrEnum):
    SUCCESS = auto()
    NOT_STARTED = auto()
    FAILURE = auto()
    ERROR = auto()
    TIMEOUT = auto()
