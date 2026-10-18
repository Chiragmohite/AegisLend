import pytest
from pydantic import ValidationError
from app.config import Settings


def test_password_and_port_validation():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, db_password="")
    with pytest.raises(ValidationError):
        Settings(_env_file=None, db_password="test", db_port=70000)


def test_special_characters_are_not_url_interpolated():
    settings = Settings(_env_file=None, db_password="a@b:/%c")
    assert settings.database_url.password == "a@b:/%c"
    assert "a@b:/%c" not in repr(settings)
    assert settings.database_url.drivername == "mysql+pymysql"


def test_unverified_llm_and_wildcard_cors_rejected():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, db_password="test", llm_provider="astra")
    with pytest.raises(ValidationError):
        Settings(_env_file=None, db_password="test", cors_origins=["*"])
