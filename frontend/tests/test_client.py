from unittest.mock import MagicMock, patch

import pytest

from app.client import BackendClient


@pytest.fixture
def client() -> BackendClient:
    return BackendClient()


def test_send_message_returns_content(client: BackendClient) -> None:
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(
        return_value={"role": "assistant", "content": "S3 is object storage."}
    )

    with patch.object(client._http, "post", return_value=mock_resp):
        result = client.send_message("s1", "What is S3?")

    assert result == "S3 is object storage."


def test_send_message_calls_correct_endpoint(client: BackendClient) -> None:
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value={"role": "assistant", "content": "ok"})

    with patch.object(client._http, "post", return_value=mock_resp) as mock_post:
        client.send_message("s1", "hello")

    mock_post.assert_called_once_with(
        "/chat", json={"session_id": "s1", "message": "hello"}
    )


def test_get_history_returns_messages(client: BackendClient) -> None:
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(
        return_value={
            "session_id": "s1",
            "messages": [{"role": "user", "content": "hi"}],
        }
    )

    with patch.object(client._http, "get", return_value=mock_resp):
        messages = client.get_history("s1")

    assert messages == [{"role": "user", "content": "hi"}]


def test_clear_history_calls_delete(client: BackendClient) -> None:
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()

    with patch.object(client._http, "delete", return_value=mock_resp) as mock_del:
        client.clear_history("s1")

    mock_del.assert_called_once_with("/chat/s1/history")
