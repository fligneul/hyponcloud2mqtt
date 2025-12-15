from __future__ import annotations
import pytest
import responses
from unittest.mock import MagicMock
from hyponcloud2mqtt.data_fetcher import DataFetcher


@pytest.fixture
def mock_config():
    """Fixture for a mock config object."""
    config = MagicMock()
    config.http_url = "http://api.example.com"
    config.api_username = "testuser"
    config.api_password = "testpass"
    config.verify_ssl = True
    return config


@responses.activate
def test_data_fetcher_login_and_setup(mock_config):
    """Test successful login during DataFetcher initialization."""
    responses.add(
        responses.POST,
        "http://api.example.com/login",
        json={"code": 20000, "data": {"token": "test-token-12345"}},
        status=200,
    )

    fetcher = DataFetcher(mock_config, "system-1")

    assert fetcher.session.headers["Authorization"] == "Bearer test-token-12345"
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == "http://api.example.com/login"


@responses.activate
def test_data_fetcher_fetch_all_success(mock_config):
    """Test successful data fetching from all endpoints."""
    # Mock login
    responses.add(
        responses.POST,
        "http://api.example.com/login",
        json={"code": 20000, "data": {"token": "test-token"}},
        status=200,
    )
    # Mock data endpoints with realistic data structure
    responses.add(
        responses.GET,
        "http://api.example.com/plant/system-1/monitor?refresh=true",
        json={"code": 20000, "data": {"power_pv": 123, "percent": 50}},
        status=200,
    )
    responses.add(
        responses.GET,
        "http://api.example.com/plant/system-1/production2",
        json={"code": 20000, "data": {"today_generation": 45.6}},
        status=200,
    )
    responses.add(
        responses.GET,
        "http://api.example.com/plant/system-1/status",
        json={"code": 20000, "data": {"gateway": {"online": 1}}},
        status=200,
    )

    fetcher = DataFetcher(mock_config, "system-1")
    merged_data = fetcher.fetch_all()

    assert merged_data is not None
    assert merged_data["power_pv"] == 123
    assert merged_data["today_generation"] == 45.6
    assert merged_data["gateway"]["online"] == 1
    # 1 login + 3 data calls
    assert len(responses.calls) == 4


@responses.activate
def test_data_fetcher_relogin_flow(mock_config):
    """Test the full re-authentication flow upon token expiration."""
    # Initial login (success)
    responses.add(
        responses.POST,
        "http://api.example.com/login",
        json={"code": 20000, "data": {"token": "token-1"}},
        status=200,
    )

    # First fetch fails with auth error
    responses.add(
        responses.GET,
        "http://api.example.com/plant/system-1/monitor?refresh=true",
        json={"code": 50008, "message": "Token expired"},
        status=200,
    )
    responses.add(
        responses.GET,
        "http://api.example.com/plant/system-1/production2",
        json={"code": 50008, "message": "Token expired"},
        status=200,
    )
    responses.add(
        responses.GET,
        "http://api.example.com/plant/system-1/status",
        json={"code": 50008, "message": "Token expired"},
        status=200,
    )

    # Re-login (success)
    responses.add(
        responses.POST,
        "http://api.example.com/login",
        json={"code": 20000, "data": {"token": "token-2"}},
        status=200,
    )

    # Second fetch attempt (success)
    responses.add(
        responses.GET,
        "http://api.example.com/plant/system-1/monitor?refresh=true",
        json={"code": 20000, "data": {"power_pv": 789}},
        status=200,
    )
    responses.add(
        responses.GET,
        "http://api.example.com/plant/system-1/production2",
        json={"code": 20000, "data": {"today_generation": 10.1}},
        status=200,
    )
    responses.add(
        responses.GET,
        "http://api.example.com/plant/system-1/status",
        json={"code": 20000, "data": {"gateway": {"online": 1}}},
        status=200,
    )

    fetcher = DataFetcher(mock_config, "system-1")

    # The first call to fetch_all should trigger the re-login and succeed
    merged_data = fetcher.fetch_all()

    assert merged_data is not None
    assert merged_data["power_pv"] == 789

    # Calls: 1 initial login, 3 failed fetches, 1 re-login, 3 successful fetches
    assert len(responses.calls) == 8
    # Check that token was updated
    assert fetcher.session.headers["Authorization"] == "Bearer token-2"


@responses.activate
def test_data_fetcher_relogin_fails(mock_config):
    """Test when re-authentication fails after a token expiry."""
    # Initial login (success)
    responses.add(
        responses.POST,
        "http://api.example.com/login",
        json={"code": 20000, "data": {"token": "token-1"}},
        status=200,
    )

    # First fetch fails with auth error
    responses.add(
        responses.GET,
        "http://api.example.com/plant/system-1/monitor?refresh=true",
        json={"code": 50008, "message": "Token expired"},
        status=200,
    )
    responses.add(
        responses.GET,
        "http://api.example.com/plant/system-1/production2",
        json={"code": 50008, "message": "Token expired"},
        status=200,
    )
    responses.add(
        responses.GET,
        "http://api.example.com/plant/system-1/status",
        json={"code": 50008, "message": "Token expired"},
        status=200,
    )

    # Re-login (fails)
    responses.add(
        responses.POST,
        "http://api.example.com/login",
        json={"code": 50001, "message": "Invalid credentials"},
        status=200,
    )

    fetcher = DataFetcher(mock_config, "system-1")
    merged_data = fetcher.fetch_all()

    assert merged_data is None
    # Calls: 1 initial login, 3 failed fetches, 1 failed re-login
    assert len(responses.calls) == 5
