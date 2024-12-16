import logging
import time

from .coapp import Validator
from .net import Loop
from .ping import Pinger

logger = logging.getLogger(__name__)


def fuzz(target, files, timeout, delay):
    validator = Validator(target)
    pinger = Pinger(host=target[0], count=5)  # TODO ping configurable?

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
            pinger.check_alive(timeout)

            time.sleep(delay)

    coapp_result = validator.total_errors()
    logger.info(f"Total COAPP errors: {coapp_result}")

    ping_result = pinger.total_errors()
    logger.info(f"Totoal ping errors: {ping_result}")

    return coapp_result + ping_result
