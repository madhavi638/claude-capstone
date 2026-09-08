import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_user: str
    db_password: str
    db_name: str
    db_host: str
    db_port: str

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


def get_settings() -> Settings:
    return Settings(
        db_user=os.environ.get("HMS6_DB_USER", "hms6_user"),
        db_password=os.environ.get("HMS6_DB_PASSWORD", "changeme"),
        db_name=os.environ.get("HMS6_DB_NAME", "hms6_appointments"),
        db_host=os.environ.get("HMS6_DB_HOST", "localhost"),
        db_port=os.environ.get("HMS6_DB_PORT", "5432"),
    )
