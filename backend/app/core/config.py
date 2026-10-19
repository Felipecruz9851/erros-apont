import os
from typing import List
from pydantic import BaseModel, Field


class Settings(BaseModel):
    PROJECT_NAME: str = "Erros de Apontamento"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Intranet default host
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

    # CORS Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ]


settings = Settings()
