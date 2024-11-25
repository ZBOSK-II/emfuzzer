import logging
import time

from .coapp import Validator
from .net import Loop

logger = logging.getLogger(__name__)


def fuzz(target, files, timeout, delay):
    validator = Validator(target)

    with Loop(validator) as loop:
        for path in files:
            logger.info(f"Opening {path}")
            with path.open("rb") as file:
                data = file.read()
            if len(data) == 0:
                logger.warn(f"No data found, skipping {path}")
                continue

            loop.send(target, data)

            validator.wait_for_validation(timeout)

            time.sleep(delay)

    result = validator.total_errors()

    logger.info(f"Total errors: {result}")

    return result
