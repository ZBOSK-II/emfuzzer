from typing import Protocol

from .Address import Address


class Validator(Protocol):

    def validate(self, addr: Address, data: bytes) -> None:
        pass

    def mark_sent(self, addr: Address, data: bytes) -> None:
        pass
