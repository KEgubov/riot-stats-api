from pathlib import Path
from pydantic_settings import SettingsConfigDict, BaseSettings
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )

    API_KEY: str = Field(..., alias="API_KEY")


    @property
    def api_key(self):
        return self.API_KEY


settings = Settings()