import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

CURRENT_FILE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_FILE_DIR.parent
ENV_PATH = CURRENT_FILE_DIR / ".env"

#print(f"📂 Looking for config in: {CURRENT_FILE_DIR}")
if ENV_PATH.exists():
    #print(f"✅ Found .env at: {ENV_PATH}")
    load_dotenv(dotenv_path=ENV_PATH, override=True)
else:
    ROOT_ENV = PROJECT_ROOT / ".env"
    if ROOT_ENV.exists():
        #print(f"⚠️ .env not found in app/, found in root: {ROOT_ENV}")
        ENV_PATH = ROOT_ENV
        load_dotenv(dotenv_path=ENV_PATH, override=True)

DATA_DIR = PROJECT_ROOT / "data"

class Settings(BaseSettings):
    OPENAI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    #"llama-3.3-70b-versatile" / "openai/gpt-oss-120b"
    LLM_MODEL: str = "openai/gpt-oss-120b" 
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    BASE_DIR: Path = PROJECT_ROOT
    DATA_DIR: Path = DATA_DIR

    @property
    def MENU_DEALS_PATH(self) -> Path: return self.DATA_DIR / "menu_deals.yaml"
    @property
    def MENU_INGREDIENTS_PATH(self) -> Path: return self.DATA_DIR / "menu_ingredients.yaml"
    @property
    def MENU_UPSELLS_PATH(self) -> Path: return self.DATA_DIR / "menu_upsells.yaml"
    @property
    def MENU_VIRTUAL_PATH(self) -> Path: return self.DATA_DIR / "menu_virtual_items.yaml"

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

settings = Settings()