import os
from typing import List
from pydantic import BaseModel, Field


def _load_env_file() -> None:
    """Carrega variáveis do arquivo .env na raiz do projeto, se existir."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    env_path = os.path.join(root_dir, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass


_load_env_file()


class Settings(BaseModel):
    PROJECT_NAME: str = "Erros de Apontamento"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Intranet default host and endpoints
    INTRANET_HOST: str = Field(
        default_factory=lambda: os.getenv("INTRANET_HOST", "http://192.168.0.6")
    )
    INTRANET_BASE_URL: str = Field(
        default_factory=lambda: os.getenv("INTRANET_BASE_URL", "http://192.168.0.6/pcp")
    )
    DEFAULT_COD_EMPRESA: str = "11"

    # Snapshot storage directory
    SNAPSHOT_DIR: str = Field(
        default_factory=lambda: os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "storage",
            "snapshots",
        )
    )

    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "8484")))

    # Contacts storage file
    CONTACTS_FILE: str = Field(
        default_factory=lambda: os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "storage",
            "contacts.json",
        )
    )

    # Sent emails log file
    SENT_EMAILS_FILE: str = Field(
        default_factory=lambda: os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "storage",
            "sent_emails.json",
        )
    )

    # SMTP Configuration
    SMTP_HOST: str = Field(default_factory=lambda: os.getenv("SMTP_HOST", ""))
    SMTP_PORT: int = Field(default_factory=lambda: int(os.getenv("SMTP_PORT", "587")))
    SMTP_USER: str = Field(default_factory=lambda: os.getenv("SMTP_USER", ""))
    SMTP_PASSWORD: str = Field(default_factory=lambda: os.getenv("SMTP_PASSWORD", ""))
    SMTP_FROM: str = Field(default_factory=lambda: os.getenv("SMTP_FROM", "pcp@liderinteriores.com.br"))
    SMTP_USE_TLS: bool = Field(default_factory=lambda: os.getenv("SMTP_USE_TLS", "true").lower() in ["true", "1"])
    SMTP_SIMULATION_MODE: bool = Field(default_factory=lambda: os.getenv("SMTP_SIMULATION_MODE", "false").lower() in ["true", "1"])

    # CORS Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8484",
        "http://127.0.0.1:8484",
    ]


settings = Settings()
