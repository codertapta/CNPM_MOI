import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.mark.parametrize("environment", ["staging", "production"])
@pytest.mark.parametrize("secret", [None, "", "   "])
def test_missing_jwt_secret_fails_fast(environment, secret):
    with pytest.raises(
        ValidationError,
        match="JWT_SECRET is required",
    ):
        Settings(
            _env_file=None,
            ENVIRONMENT=environment,
            JWT_SECRET=secret,
        )


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_valid_jwt_secret_allows_startup(environment):
    settings = Settings(
        _env_file=None,
        ENVIRONMENT=environment,
        JWT_SECRET="test-secret-for-automated-tests",
    )

    assert settings.ENVIRONMENT == environment


def test_development_allows_missing_jwt_secret():
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="development",
        JWT_SECRET=None,
    )

    assert settings.JWT_SECRET is None
