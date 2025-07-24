import pytest
from unittest.mock import patch, MagicMock
from src.hyponcloud2mqtt.hypon_cloud import (
    HyponCloudClient,
    MonitorData,
    HyponAuthenticationError,
    HyponRequestError,
    HyponAPIError,
)
import requests


@pytest.fixture
def mock_config():
    return {
        "hypon": {
            "user": "test_user",
            "password": "test_password",
            "api_base_url": "https://api.example.com",
        }
    }


@pytest.fixture
def hypon_client(mock_config):
    return HyponCloudClient(mock_config)


def test_login_success(hypon_client):
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 20000,
            "data": {"token": "test_token"},
        }
        mock_post.return_value = mock_response

        hypon_client.login()
        assert hypon_client.token == "test_token"


def test_login_failure_invalid_credentials(hypon_client):
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 40000,
            "message": "Invalid credentials",
        }
        mock_post.return_value = mock_response

        with pytest.raises(
            HyponAuthenticationError, match="Login failed: Invalid credentials"
        ):
            hypon_client.login()
        assert hypon_client.token is None


def test_login_failure_request_exception(hypon_client):
    with patch(
        "requests.post",
        side_effect=requests.exceptions.RequestException("Network error"),
    ):
        with pytest.raises(
            HyponRequestError, match="Error during login request: Network error"
        ):
            hypon_client.login()
        assert hypon_client.token is None


def test_get_data_success(hypon_client):
    hypon_client.token = "existing_token"
    system_ids = ["sys1", "sys2"]
    with patch("requests.get") as mock_get:
        mock_response_sys1 = MagicMock()
        mock_response_sys1.status_code = 200
        mock_response_sys1.json.return_value = {
            "code": 20000,
            "data": {
                "monetary": "USD",
                "today_earning": 10.0,
                "month_earning": 100.0,
                "total_earning": 1000.0,
                "e_total": 5000.0,
                "e_month": 500.0,
                "e_today": 50.0,
                "e_year": 2000.0,
                "total_tree": 5,
                "total_co2": 10,
                "total_diesel": 20,
                "percent": 90.0,
                "meter_power": 5.0,
                "power_load": 2.0,
                "w_cha": 1.0,
                "power_pv": 3.0,
                "soc": 80.0,
                "micro": 0.5,
            },
        }

        mock_response_sys2 = MagicMock()
        mock_response_sys2.status_code = 200
        mock_response_sys2.json.return_value = {
            "code": 20000,
            "data": {
                "monetary": "EUR",
                "today_earning": 12.0,
                "month_earning": 120.0,
                "total_earning": 1200.0,
                "e_total": 6000.0,
                "e_month": 600.0,
                "e_today": 60.0,
                "e_year": 2400.0,
                "total_tree": 6,
                "total_co2": 12,
                "total_diesel": 24,
                "percent": 95.0,
                "meter_power": 6.0,
                "power_load": 2.5,
                "w_cha": 1.2,
                "power_pv": 3.5,
                "soc": 85.0,
                "micro": 0.6,
            },
        }

        mock_get.side_effect = [mock_response_sys1, mock_response_sys2]

        all_monitor_data = hypon_client.get_data(system_ids)

        assert len(all_monitor_data) == 2
        assert isinstance(all_monitor_data["sys1"], MonitorData)
        assert all_monitor_data["sys1"].monetary == "USD"
        assert isinstance(all_monitor_data["sys2"], MonitorData)
        assert all_monitor_data["sys2"].monetary == "EUR"


def test_get_data_retry_on_api_error(hypon_client):
    hypon_client.token = "existing_token"
    system_ids = ["sys1"]

    with (
        patch("requests.get") as mock_get,
        patch.object(hypon_client, "login") as mock_login,
    ):

        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 200
        mock_response_fail.json.return_value = {
            "code": 50000,
            "message": "Internal Server Error",
        }

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "code": 20000,
            "data": {
                "monetary": "USD",
                "today_earning": 10.0,
                "month_earning": 100.0,
                "total_earning": 1000.0,
                "e_total": 5000.0,
                "e_month": 500.0,
                "e_today": 50.0,
                "e_year": 2000.0,
                "total_tree": 5,
                "total_co2": 10,
                "total_diesel": 20,
                "percent": 90.0,
                "meter_power": 5.0,
                "power_load": 2.0,
                "w_cha": 1.0,
                "power_pv": 3.0,
                "soc": 80.0,
                "micro": 0.5,
            },
        }

        mock_get.side_effect = [mock_response_fail, mock_response_success]

        all_monitor_data = hypon_client.get_data(system_ids, retries=1)

        assert mock_login.call_count == 1
        assert len(all_monitor_data) == 1
        assert isinstance(all_monitor_data["sys1"], MonitorData)


def test_get_data_fail_after_multiple_retries(hypon_client):
    hypon_client.token = "existing_token"
    system_ids = ["sys1"]

    with (
        patch("requests.get") as mock_get,
        patch.object(hypon_client, "login") as mock_login,
    ):

        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 200
        mock_response_fail.json.return_value = {
            "code": 50000,
            "message": "Internal Server Error",
        }

        mock_get.return_value = mock_response_fail

        all_monitor_data = hypon_client.get_data(system_ids, retries=3)

        assert mock_login.call_count == 3
        assert len(all_monitor_data) == 1
        assert all_monitor_data["sys1"] is None


def test_get_data_retry_on_http_error(hypon_client):
    hypon_client.token = "existing_token"
    system_ids = ["sys1"]

    with (
        patch("requests.get") as mock_get,
        patch.object(hypon_client, "login") as mock_login,
    ):

        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "code": 20000,
            "data": {
                "monetary": "USD",
                "today_earning": 10.0,
                "month_earning": 100.0,
                "total_earning": 1000.0,
                "e_total": 5000.0,
                "e_month": 500.0,
                "e_today": 50.0,
                "e_year": 2000.0,
                "total_tree": 5,
                "total_co2": 10,
                "total_diesel": 20,
                "percent": 90.0,
                "meter_power": 5.0,
                "power_load": 2.0,
                "w_cha": 1.0,
                "power_pv": 3.0,
                "soc": 80.0,
                "micro": 0.5,
            },
        }

        mock_get.side_effect = [mock_response_fail, mock_response_success]

        all_monitor_data = hypon_client.get_data(system_ids, retries=1)

        assert mock_login.call_count == 1
        assert len(all_monitor_data) == 1
        assert isinstance(all_monitor_data["sys1"], MonitorData)
