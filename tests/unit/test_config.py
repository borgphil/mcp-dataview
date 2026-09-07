import pytest
from app.config import DatabaseSettings


def test_non_sample_database_requires_read_only(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///external.db")
    monkeypatch.setenv("DATABASE_READ_ONLY", "false")
    with pytest.raises(RuntimeError, match="DATABASE_READ_ONLY"):
        DatabaseSettings.from_environment()


def test_sample_database_is_selected_without_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = DatabaseSettings.from_environment()
    assert settings.sample is True
