import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Resolve paths relative to this file's location (backend/app/)
_APP_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _APP_DIR.parent
_PROJECT_DIR = _BACKEND_DIR.parent


def _in_docker() -> bool:
    """Detect if running inside a Docker container."""
    return os.path.exists("/.dockerenv")


class Settings(BaseSettings):
    # Database
    database_url: str = ""

    # MQTT defaults
    mqtt_port: int = 8883

    # App
    app_name: str = "Filament Manager"
    debug: bool = False

    # Paths
    data_dir: str = ""
    config_dir: str = ""

    model_config = {"env_prefix": "FM_", "env_file": ".env"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.data_dir:
            if _in_docker():
                candidates = [Path("/app/data")]
            else:
                candidates = [
                    _PROJECT_DIR / "data",
                    _BACKEND_DIR / "data",
                ]
            for p in candidates:
                p.mkdir(parents=True, exist_ok=True)
                if p.is_dir():
                    self.data_dir = str(p)
                    break

        if not self.database_url:
            db_path = os.path.join(self.data_dir, "filament.db")
            self.database_url = f"sqlite:///{db_path}"

        if not self.config_dir:
            if _in_docker():
                config_dir = Path("/app/config")
            else:
                config_dir = _PROJECT_DIR / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_dir = str(config_dir)


settings = Settings()
