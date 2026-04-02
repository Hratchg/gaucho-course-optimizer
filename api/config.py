from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    database_url: str = "postgresql://gco:gco@localhost:5432/gco"
    rmp_auth_token: str = ""
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    def get_origins(self) -> list[str]:
        """Parse comma-separated allowed_origins into a list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
