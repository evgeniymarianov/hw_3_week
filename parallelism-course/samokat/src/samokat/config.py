from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseModel):
    host: str
    port: int
    reload: bool


class PostgresConfig(BaseModel):
    host: str
    port: int
    user: str
    password: SecretStr
    database: str

    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20

    @property
    def url(self) -> str:
        return (
            f"postgresql+psycopg://{self.user}:"
            f"{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.database}"
        )


class RedisConfig(BaseModel):
    host: str
    port: int
    password: SecretStr | None = None
    database: int = 0

    @property
    def url(self) -> str:
        if self.password is None:
            return f"redis://{self.host}:{self.port}/{self.database}"

        password = self.password.get_secret_value()
        return f"redis://:{password}@{self.host}:{self.port}/{self.database}"


class ClickHouseConfig(BaseModel):
    host: str
    port: int
    username: str
    password: SecretStr
    database: str
    secure: bool = False
    compress: bool = True


class TokenConfig(BaseModel):
    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30


class CorsConfig(BaseModel):
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ],
    )


class ProfilingConfig(BaseModel):
    enabled: bool = True
    pyinstrument_enabled: bool = True
    line_profiler_enabled: bool = True
    interval: float = 0.001
    output_directory: str = "profiles/pyinstrument"
    public_path: str = "/__profiles"


class AddressApiConfig(BaseModel):
    base_url: str
    client_id: str
    client_secret: SecretStr
    timeout: float = 5.0


class DarkstoreApiConfig(BaseModel):
    base_url: str
    api_key: SecretStr
    timeout: float = 5.0


class DeliveryApiConfig(BaseModel):
    base_url: str
    api_key: SecretStr
    timeout: float = 5.0


class ConnectorsConfig(BaseModel):
    address: AddressApiConfig
    darkstore: DarkstoreApiConfig
    delivery: DeliveryApiConfig


class ReportsConfig(BaseModel):
    directory: str = "reports"


class KafkaConfig(BaseModel):
    bootstrap_servers: str = "localhost:9092"
    tracking_topic: str = "delivery.tracking"


class Settings(BaseSettings):
    app: AppConfig
    postgres: PostgresConfig
    redis: RedisConfig
    clickhouse: ClickHouseConfig
    token: TokenConfig
    cors: CorsConfig = Field(default_factory=CorsConfig)
    profiling: ProfilingConfig = Field(default_factory=ProfilingConfig)
    connectors: ConnectorsConfig
    reports: ReportsConfig = Field(default_factory=ReportsConfig)
    kafka: KafkaConfig = Field(default_factory=KafkaConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )
