import socket

from pydantic import model_validator
from pydantic_settings import BaseSettings


def _host_resolves(hostname: str) -> bool:
    try:
        socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False
    return True


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str

    model_config = {"env_file": ".env", "extra": "ignore"}

    @model_validator(mode="after")
    def normalize_local_database_url(self) -> "Settings":
        if "@db:" in self.DATABASE_URL and not _host_resolves("db"):
            self.DATABASE_URL = self.DATABASE_URL.replace("@db:", "@localhost:", 1)
        return self


settings = Settings()
