import logging
import threading
from enum import StrEnum, auto

from ..net import Validator as Base
from .code import code_reports_success, code_to_string, decode_code

logger = logging.getLogger(__name__)


class Validator(Base):

    class Result(StrEnum):
        SUCCESS = auto()
        UNKNOWN = auto()
        UNEXPECTED_ORIGIN = auto()
        TOO_SHORT_MESSAGE = auto()
        FAILED_OPERATIONS = auto()
        TIMEDOUT = auto()

    def __init__(self, expected_ip: str):
        self.expected_ip = expected_ip

        self.expecting_event = threading.Event()
        self.validation_complete_cv = threading.Condition()

        self.last_result: Validator.Result = self.Result.UNKNOWN

        self.unexpected_messages = 0

    def validate(self, addr: str, data: bytes) -> None:
        if not self.expecting_event.is_set():
            self.__unexpected_message()
            return
        self.expecting_event.clear()
        self.last_result = self.check_message(addr, data)
        with self.validation_complete_cv:
            self.validation_complete_cv.notify()

    def check_message(self, addr: str, data: bytes) -> Result:
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

    def mark_sent(self, addr: str, data: bytes) -> None:
        self.last_result = self.Result.UNKNOWN
        self.expecting_event.set()

    def wait_for_result(self, timeout: int = 5) -> Result:
        with self.validation_complete_cv:
            if not self.validation_complete_cv.wait_for(
                lambda: self.last_result != self.Result.UNKNOWN, timeout=timeout
            ):
                logger.warn("Operation timed out")
                return self.Result.TIMEDOUT

        return self.last_result

    def __unexpected_message(self) -> None:
        logger.warn("Message unexpected at this stage")
        self.unexpected_messages += 1
