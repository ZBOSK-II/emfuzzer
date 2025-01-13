import logging
import threading

from .code import code_reports_success, code_to_string, decode_code

logger = logging.getLogger(__name__)


class Validator:

    def __init__(self, expected_ip: str):
        self.expected_ip = expected_ip

        self.expecting_event = threading.Event()
        self.validation_complete = threading.Event()
        self.validation_complete_cv = threading.Condition()

        self.total = 0
        self.unexpected_origin = 0
        self.unexpected_message = 0
        self.too_short_message = 0
        self.failed_operations = 0
        self.timedout_operations = 0

    def __call__(self, addr: str, data: bytes) -> None:
        self.validate(addr, data)
        self.validation_complete.set()
        with self.validation_complete_cv:
            self.validation_complete_cv.notify()

    def validate(self, addr: str, data: bytes) -> None:
        self.total += 1

        if addr != self.expected_ip:
            logger.warn(
                f"Message received from unexpected origin: {addr} vs {self.expected_ip}"
            )
            self.unexpected_origin += 1
            return

        if len(data) < 2:
            logger.warn("Too short message")
            self.too_short_message += 1
            return

        code = decode_code(data[1])

        logger.info(f"Received {code_to_string(code)}")

        if not self.expecting_event.is_set():
            logger.warn("Message unexpected at this stage")
            self.unexpected_message += 1
            return

        if not code_reports_success(code):
            logger.warn("Operation reported as failed")
            self.failed_operations += 1
            return

    def wait_for_validation(self, timeout: int = 5) -> None:
        self.expecting_event.set()
        self.validation_complete.clear()

        with self.validation_complete_cv:
            if not self.validation_complete_cv.wait_for(
                lambda: self.validation_complete.is_set(), timeout=timeout
            ):
                logger.warn("Operation timed out")
                self.timedout_operations += 1

        self.expecting_event.clear()
        self.validation_complete.clear()

    def total_errors(self) -> int:
        return (
            self.unexpected_origin
            + self.unexpected_message
            + self.too_short_message
            + self.failed_operations
            + self.timedout_operations
        )
