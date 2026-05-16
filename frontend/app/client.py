from pathlib import Path

import httpx
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).parents[2] / ".env"


class _Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )
    backend_url: str = "http://localhost:8000"


_settings = _Settings()


class BackendClient:
    def __init__(self) -> None:
        self._http = httpx.Client(base_url=_settings.backend_url, timeout=120.0)

    def send_message(self, session_id: str, message: str) -> str:
        response = self._http.post(
            "/chat", json={"session_id": session_id, "message": message}
        )
        response.raise_for_status()
        return response.json()["content"]  # type: ignore[no-any-return]

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        response = self._http.get(f"/chat/{session_id}/history")
        response.raise_for_status()
        return response.json()["messages"]  # type: ignore[no-any-return]

    def clear_history(self, session_id: str) -> None:
        response = self._http.delete(f"/chat/{session_id}/history")
        response.raise_for_status()
