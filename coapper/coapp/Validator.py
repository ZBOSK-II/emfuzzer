import logging
import threading
from enum import StrEnum, auto

from ..net import Address
from ..net import Consumer
from .code import code_reports_success, code_to_string, decode_code

logger = logging.getLogger(__name__)


class Validator(Consumer):

    class Result(StrEnum):
        SUCCESS = auto()
        UNKNOWN = auto()
        UNEXPECTED_ORIGIN = auto()
        TOO_SHORT_MESSAGE = auto()
        FAILED_OPERATIONS = auto()
        TIMEDOUT = auto()

    def __init__(self, expected_ip: Address, timeout: float):
        self.expected_ip = expected_ip
        self.timeout = timeout

        self.expecting_event = threading.Event()
        self.validation_complete_cv = threading.Condition()

        self.last_result: Validator.Result = self.Result.UNKNOWN

        self.unexpected_messages = 0

    def on_received(self, addr: Address, data: bytes) -> None:
        if not self.expecting_event.is_set():
            self.__unexpected_message()
            return
        self.expecting_event.clear()
        self.last_result = self.check_message(addr, data)
        with self.validation_complete_cv:
            self.validation_complete_cv.notify()

    def check_message(self, addr: Address, data: bytes) -> Result:
        if addr != self.expected_ip:
            logger.warn(
                f"Message received from unexpected origin: {addr} vs {self.expected_ip}"
            )
            return self.Result.UNEXPECTED_ORIGIN

        if len(data) < 2:
            logger.warn("Too short message")
            return self.Result.TOO_SHORT_MESSAGE

        code = decode_code(data[1])

        logger.info(f"Received {code_to_string(code)}")

        if not code_reports_success(code):
            logger.warn("Operation reported as failed")
            return self.Result.FAILED_OPERATIONS

        return self.Result.SUCCESS

    def on_sent(self, addr: Address, data: bytes) -> None:
        self.last_result = self.Result.UNKNOWN
        self.expecting_event.set()

    def wait_for_result(self) -> Result:
        with self.validation_complete_cv:
            if not self.validation_complete_cv.wait_for(
                lambda: self.last_result != self.Result.UNKNOWN, timeout=self.timeout
            ):
                logger.warn("Operation timed out")
                self.expecting_event.clear()
                return self.Result.TIMEDOUT

        result = self.last_result
        self.last_result = self.Result.UNKNOWN
        return result

    def extra_stats(self) -> dict[str, int]:
        return {"unexpected_messages": self.unexpected_messages}

    def __unexpected_message(self) -> None:
        logger.warn("Message unexpected at this stage")
        self.unexpected_messages += 1
