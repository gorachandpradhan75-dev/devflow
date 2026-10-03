"""Application configuration. All secrets come from environment variables."""
import os


def build_database_url():
    """Build the PostgreSQL URL from environment variables (never hardcoded)."""
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url
    user = os.getenv("POSTGRES_USER", "devflow")
    password = os.getenv("POSTGRES_PASSWORD", "")
    host = os.getenv("POSTGRES_HOST", "db")
    port = os.getenv("POSTGRES_PORT", "5432")
    name = os.getenv("POSTGRES_DB", "devflow")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


class Config:
    SQLALCHEMY_DATABASE_URI = build_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")


class TestConfig(Config):
    """Tests use an in-memory SQLite database so they run anywhere (e.g. Jenkins)."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
