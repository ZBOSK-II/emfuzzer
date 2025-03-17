from dataclasses import dataclass


@dataclass
class ConnectionConfig:
    host: str
    port: int
    username: str
    password: str
