from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    delta_base_path: str = "./warehouse"
    delta_refresh_seconds: float = 2.0


settings = Settings()
