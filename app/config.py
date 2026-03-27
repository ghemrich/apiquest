from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Postgres
    POSTGRES_USER: str = "apiquest"
    POSTGRES_PASSWORD: str = "apiquest_secret"
    POSTGRES_DB: str = "apiquest"
    DATABASE_URL: str = "postgresql://apiquest:apiquest_secret@localhost:5432/apiquest"

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # App
    APP_ENV: str = "development"
    DEBUG: bool = True

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
