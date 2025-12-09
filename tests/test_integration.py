from __future__ import annotations
# import pytest
import pytest
import responses
from hyponcloud2mqtt.http_client import HttpClient, AuthenticationError


@responses.activate
def test_login_success():
    """Test successful login with correct credentials."""
    import json

    responses.add(
        responses.POST,
        "http://api.example.com/login",
        json={"code": 20000, "data": {"token": "test-token-12345"}},
        status=200
    )

    token = HttpClient.login("http://api.example.com", "testuser", "testpass")

    assert token == "test-token-12345"
    assert len(responses.calls) == 1
    request_body = json.loads(responses.calls[0].request.body)
    assert request_body == {
        "username": "testuser",
        "password": "testpass",
        "oem": None
    }


@responses.activate
def test_login_failure_wrong_code():
    """Test login failure with wrong code."""
    responses.add(
        responses.POST,
        "http://api.example.com/login",
        json={"code": 50001, "message": "Invalid credentials"},
        status=200
    )

    token = HttpClient.login("http://api.example.com", "baduser", "badpass")

    assert token is None


@responses.activate
def test_fetch_data_with_valid_token():
    """Test fetching data with a valid Bearer token."""
    responses.add(
        responses.GET,
        "http://api.example.com/monitor",
        json={"code": 20000, "data": {"power_pv": 100}},
        status=200
    )

    client = HttpClient("http://api.example.com/monitor", "valid-token")
    data = client.fetch_data()

    assert data == {"code": 20000, "data": {"power_pv": 100}}
    assert len(responses.calls) == 1
    assert responses.calls[0].request.headers["Authorization"] == "Bearer valid-token"


@responses.activate
def test_fetch_data_expired_token():
    """Test fetching data with expired token (code 50008)."""
    responses.add(
        responses.GET,
        "http://api.example.com/monitor",
        json={"code": 50008, "message": "User authentication failed"},
        status=200
    )

    client = HttpClient("http://api.example.com/monitor", "expired-token")

    with pytest.raises(AuthenticationError):
        client.fetch_data()


@responses.activate
def test_fetch_data_without_token():
    """Test fetching data without authentication."""
    responses.add(
        responses.GET,
        "http://api.example.com/monitor",
        json={"code": 50008, "message": "User authentication failed"},
        status=200
    )

    client = HttpClient("http://api.example.com/monitor", None)

    with pytest.raises(AuthenticationError):
        client.fetch_data()


@responses.activate
def test_full_auth_flow():
    """Test complete authentication flow: login -> fetch -> token expired -> re-login -> fetch."""
    # First login
    responses.add(
        responses.POST,
        "http://api.example.com/login",
        json={"code": 20000, "data": {"token": "token-1"}},
        status=200
    )

    # First fetch succeeds
    responses.add(
        responses.GET,
        "http://api.example.com/data",
        json={"code": 20000, "data": {"value": 42}},
        status=200
    )

    # Second fetch fails (token expired)
    responses.add(
        responses.GET,
        "http://api.example.com/data",
        json={"code": 50008, "message": "User authentication failed"},
        status=200
    )

    # Re-login
    responses.add(
        responses.POST,
        "http://api.example.com/login",
        json={"code": 20000, "data": {"token": "token-2"}},
        status=200
    )

    # Third fetch succeeds with new token
    responses.add(
        responses.GET,
        "http://api.example.com/data",
        json={"code": 20000, "data": {"value": 43}},
        status=200
    )

    # Simulate the flow
    token = HttpClient.login("http://api.example.com", "user", "pass")
    assert token == "token-1"

    client = HttpClient("http://api.example.com/data", token)
    data = client.fetch_data()
    assert data["data"]["value"] == 42

    # Token expires
    with pytest.raises(AuthenticationError):
        client.fetch_data()

    # Re-login
    new_token = HttpClient.login("http://api.example.com", "user", "pass")
    assert new_token == "token-2"

    client.update_token(new_token)
    data = client.fetch_data()
    assert data["data"]["value"] == 43


@responses.activate
def test_fetch_data_generic_error():
    """Test fetching data with a generic error (not 50008)."""
    responses.add(
        responses.GET,
        "http://api.example.com/monitor",
        json={"code": 50001, "message": "Server error"},
        status=200
    )

    client = HttpClient("http://api.example.com/monitor", "valid-token")
    data = client.fetch_data()

    assert data is None
