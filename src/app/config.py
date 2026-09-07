import os
from dataclasses import dataclass

@dataclass(frozen=True)
class DatabaseSettings:
    url: str | None
    read_only: bool
    sample: bool

    @classmethod
    def from_environment(cls) -> "DatabaseSettings":
        url = os.getenv("DATABASE_URL")
        sample = url is None
        read_only = os.getenv("DATABASE_READ_ONLY", "true").lower() in {"1", "true", "yes"}
        if not sample and not read_only:
            raise RuntimeError("DATABASE_READ_ONLY must be enabled for non-sample databases")
        return cls(url=url, read_only=read_only, sample=sample)
