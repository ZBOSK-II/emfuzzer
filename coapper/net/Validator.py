from typing import Protocol


class Validator(Protocol):

    def validate(self, addr: str, data: bytes) -> None:
        pass

    def mark_sent(self, addr: str, data: bytes) -> None:
        pass
