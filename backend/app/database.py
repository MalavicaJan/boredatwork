from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Settings(BaseSettings):
    database_url: str

    # Comma-separated list of origins allowed to call the API. The
    # default is the dev server; production must set this or the
    # deployed frontend is blocked by CORS.
    allowed_origins: str = "http://localhost:5173"

    # Must be True anywhere the site is served over HTTPS, or the
    # session cookie will also be sent over plain HTTP.
    cookie_secure: bool = False

    # "lax" is right when the API and the site share an origin, which
    # also gives CSRF protection for free. A cross-origin deployment
    # needs "none", and then the cookie must be Secure and you need a
    # CSRF token of your own.
    cookie_samesite: str = "lax"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]


settings = Settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

