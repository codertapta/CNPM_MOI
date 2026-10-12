
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "automatic_dubbing"
    GIT_SHA: str = "unknown"

    ENVIRONMENT: str = "development"
    JWT_SECRET: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_jwt_secret(self):
        environment = self.ENVIRONMENT.strip().lower()

        if environment in {"staging", "production"}:
            if not self.JWT_SECRET or not self.JWT_SECRET.strip():
                raise ValueError(
                    "JWT_SECRET is required in staging/production"
                )

        return self


settings = Settings()
