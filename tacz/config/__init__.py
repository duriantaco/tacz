import os
from pathlib import Path
import keyring
from dotenv import dotenv_values
from typing import Optional


class Config:
    def __init__(self):
        self.config_path = Path.home() / ".taczrc"
        self.vals = dotenv_values(self.config_path)
        self.keyring_service = "tacz"

    def get_tacz_dir(self):
        tacz_dir = Path.home() / ".tacz"
        tacz_dir.mkdir(exist_ok=True)
        return tacz_dir
    
    def get_db_path(self):
        return self.get_tacz_dir() / "commands.db"
    
    def get_secure_value(self, key: str, env_var: str) -> Optional[str]:
        value = os.getenv(env_var)
        if value:
            return value
        
        try:
            value = keyring.get_password(self.keyring_service, key)
            if value:
                return value
        except Exception:
            pass
        
        return self.vals.get(env_var)
    
    @property
    def ollama_base_url(self) -> str:
        return self.vals.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    
    @property
    def ollama_model(self) -> str:
        return self.vals.get("OLLAMA_MODEL", "llama3.1:8b")
    
    @property
    def cache_ttl_hours(self) -> int:
        try:
            return int(self.vals.get("CACHE_TTL_HOURS", "24"))
        except ValueError:
            return 24
    
    @property
    def enable_cache(self) -> bool:
        return self.vals.get("ENABLE_CACHE", "true").lower() == "true"
    
    @property
    def enable_history(self) -> bool:
        return self.vals.get("ENABLE_HISTORY", "true").lower() == "true"

config = Config()

def get_tacz_dir():
    return config.get_tacz_dir()

def get_db_path():
    return config.get_db_path()