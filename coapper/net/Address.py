from dataclasses import dataclass


@dataclass
class Address:
    host: str
    port: int

    def as_tuple(self) -> tuple[str, int]:
        return self.host, self.port
