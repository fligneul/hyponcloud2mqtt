from __future__ import annotations
import pytest
from unittest.mock import MagicMock
from hyponcloud2mqtt.http_client import HttpClient, AuthenticationError


def test_fetch_data_success():
    """Test fetching data successfully."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"code": 20000, "data": {"power_pv": 100}}
    mock_session.get.return_value = mock_response

    client = HttpClient("http://api.example.com/monitor", mock_session)
    data = client.fetch_data()

    assert data == {"code": 20000, "data": {"power_pv": 100}}
    mock_session.get.assert_called_once_with(
        "http://api.example.com/monitor", timeout=10)


def test_fetch_data_expired_token():
    """Test fetching data with expired token (code 50008)."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "code": 50008, "message": "User authentication failed"}
    mock_session.get.return_value = mock_response

    client = HttpClient("http://api.example.com/monitor", mock_session)

    with pytest.raises(AuthenticationError):
        client.fetch_data()


def test_fetch_data_server_error_code():
    """Test fetching data with a non-20000 non-50008 error code."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"code": 50001, "message": "Server error"}
    mock_session.get.return_value = mock_response

    client = HttpClient("http://api.example.com/monitor", mock_session)
    data = client.fetch_data()

    assert data is None


def test_fetch_data_http_error():
    """Test fetching data with an HTTP error (non-200 status code)."""
    import requests
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.HTTPError(
        "500 Server Error")
    mock_session.get.return_value = mock_response

    client = HttpClient("http://api.example.com/monitor", mock_session)
    data = client.fetch_data()

    assert data is None


def test_fetch_data_invalid_json():
    """Test fetching data that returns invalid JSON."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Simulating json() raising ValueError which is common when parsing fails
    mock_response.json.side_effect = ValueError("No JSON object could be decoded")
    mock_session.get.return_value = mock_response

    client = HttpClient("http://api.example.com/monitor", mock_session)
    data = client.fetch_data()

    assert data is None


def test_fetch_data_not_json_dict():
    """Test fetching data that returns JSON but not a dict."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = ["list", "instead", "of", "dict"]
    mock_session.get.return_value = mock_response

    client = HttpClient("http://api.example.com/monitor", mock_session)
    data = client.fetch_data()

    assert data is None
