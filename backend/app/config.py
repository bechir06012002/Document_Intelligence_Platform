from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_file_encoding="utf-8")

    azure_document_intelligence_endpoint: str
    azure_document_intelligence_key: str
    azure_openai_endpoint: str
    azure_openai_deployment: str
    azure_openai_api_key: str


settings = Settings()
