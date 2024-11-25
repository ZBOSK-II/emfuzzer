from .coapp import Validator
from .net import Loop

import logging

logger = logging.getLogger(__name__)

def fuzz(target, files):
    validator = Validator(target)

    with Loop(validator) as loop:  # TODO
        for path in files:
            logger.info(f"Opening {path}")
            with path.open("rb") as file:
                data = file.read()
            if len(data) == 0:
                logger.warn(f"No data found, skipping {path}")
                continue
            loop.send(target, data)
            validator.wait_for_validation() # TODO timeout
    return validator.total_errors()
