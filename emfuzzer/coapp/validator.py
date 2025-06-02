# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
CoAP - communication validator.
"""

import logging
import threading
from enum import StrEnum, auto

from ..io.net import NetworkAddress, NetworkObserver
from .code import code_reports_success, code_to_string, decode_code

logger = logging.getLogger(__name__)


class Validator(NetworkObserver):

    class Result(StrEnum):
        SUCCESS = auto()
        UNKNOWN = auto()
        UNEXPECTED_ORIGIN = auto()
        MESSAGE_TOO_SHORT = auto()
        OPERATION_FAILURE = auto()
        TIMEOUT = auto()

    def __init__(self, expected_ip: NetworkAddress, timeout: float):
        self.expected_ip = expected_ip
        self.timeout = timeout

        self.cond = threading.Condition()
        self.expecting = False
        self.result: Validator.Result = self.Result.UNKNOWN

        self.unexpected_messages = 0

    def on_read(self, address: NetworkAddress, data: bytes) -> None:
        with self.cond:
            if not self.expecting:
                self.__unexpected_message()
                return
            self.expecting = False
            self.result = self.check_message(address, data)
            self.cond.notify()

    def check_message(self, address: NetworkAddress, data: bytes) -> Result:
        if address != self.expected_ip:
            logger.warning(
                f"Message received from unexpected origin: {address} vs {self.expected_ip}"
            )
            return self.Result.UNEXPECTED_ORIGIN

        if len(data) < 2:
            logger.warning("Too short message")
            return self.Result.MESSAGE_TOO_SHORT

        code = decode_code(data[1])

        logger.info(f"Received {code_to_string(code)}")

        if not code_reports_success(code):
            logger.warning("Operation reported as failed")
            return self.Result.OPERATION_FAILURE

        return self.Result.SUCCESS

    def on_write(self, address: NetworkAddress, data: bytes) -> None:
        with self.cond:
            self.expecting = True
            self.result = self.Result.UNKNOWN

    def wait_for_result(self) -> Result:
        with self.cond:
            if not self.cond.wait_for(
                lambda: self.result != self.Result.UNKNOWN, timeout=self.timeout
            ):
                self.expecting = False
                logger.warning("Operation timed out")
                return self.Result.TIMEOUT
            result = self.result
            self.result = self.Result.UNKNOWN
            return result

    def extra_stats(self) -> dict[str, int]:
        return {"unexpected_messages": self.unexpected_messages}

    def __unexpected_message(self) -> None:
        logger.warning("Message unexpected at this stage")
        self.unexpected_messages += 1
