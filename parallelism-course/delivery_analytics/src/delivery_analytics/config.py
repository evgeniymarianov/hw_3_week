from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8104
    reload: bool = False


class PostgresConfig(BaseModel):
    host: str = "localhost"
    port: int = 8432
    user: str = "postgres"
    password: SecretStr = SecretStr("postgres")
    database: str = "postgres"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20

    @property
    def url(self) -> str:
        password = self.password.get_secret_value()
        return (
            f"postgresql+psycopg://{self.user}:{password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


class KafkaConfig(BaseModel):
    bootstrap_servers: str = "localhost:9092"
    tracking_topic: str = "delivery.tracking"
    group_id: str = "delivery.tracking"


class Settings(BaseSettings):
    app: AppConfig = AppConfig()
    postgres: PostgresConfig = PostgresConfig()
    kafka: KafkaConfig = KafkaConfig()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DELIVERY_ANALYTICS__",
        env_nested_delimiter="__",
        extra="ignore",
    )
