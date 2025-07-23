import pytest
from unittest.mock import patch, MagicMock
from src.hyponcloud2mqtt.hypon_cloud import HyponCloudClient, MonitorData
import requests

@pytest.fixture
def mock_config():
    return {
        "hypon": {
            "user": "test_user",
            "password": "test_password",
            "api_base_url": "https://api.example.com"
        }
    }

@pytest.fixture
def hypon_client():
    return HyponCloudClient()

def test_login_success(hypon_client, mock_config):
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 20000, "data": {"token": "test_token"}}
        mock_post.return_value = mock_response

        token = hypon_client.login(mock_config)

        mock_post.assert_called_once_with(
            f"{mock_config['hypon']['api_base_url']}/login",
            json={'username': 'test_user', 'password': 'test_password', 'oem': None},
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
            },
            timeout=30
        )
        assert token == "test_token"
        assert hypon_client.token == "test_token"

def test_login_failure_invalid_credentials(hypon_client, mock_config):
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 40000, "message": "Invalid credentials"}
        mock_post.return_value = mock_response

        token = hypon_client.login(mock_config)

        assert token is None
        assert hypon_client.token is None

def test_login_failure_request_exception(hypon_client, mock_config):
    with patch('requests.post', side_effect=requests.exceptions.RequestException("Network error")):
        token = hypon_client.login(mock_config)

        assert token is None
        assert hypon_client.token is None

def test_get_data_success(hypon_client, mock_config):
    hypon_client.token = "existing_token"
    system_ids = ["sys1", "sys2"]
    with patch('requests.get') as mock_get:
        mock_response_sys1 = MagicMock()
        mock_response_sys1.status_code = 200
        mock_response_sys1.json.return_value = {"code": 20000, "data": {"monetary": "USD", "today_earning": 10.0, "month_earning": 100.0, "total_earning": 1000.0, "e_total": 5000.0, "e_month": 500.0, "e_today": 50.0, "e_year": 2000.0, "total_tree": 5, "total_co2": 10, "total_diesel": 20, "percent": 90.0, "meter_power": 5.0, "power_load": 2.0, "w_cha": 1.0, "power_pv": 3.0, "soc": 80.0, "micro": 0.5}}

        mock_response_sys2 = MagicMock()
        mock_response_sys2.status_code = 200
        mock_response_sys2.json.return_value = {"code": 20000, "data": {"monetary": "EUR", "today_earning": 12.0, "month_earning": 120.0, "total_earning": 1200.0, "e_total": 6000.0, "e_month": 600.0, "e_today": 60.0, "e_year": 2400.0, "total_tree": 6, "total_co2": 12, "total_diesel": 24, "percent": 95.0, "meter_power": 6.0, "power_load": 2.5, "w_cha": 1.2, "power_pv": 3.5, "soc": 85.0, "micro": 0.6}}

        mock_get.side_effect = [mock_response_sys1, mock_response_sys2]

        all_monitor_data = hypon_client.get_data(mock_config, system_ids)

        assert len(all_monitor_data) == 2
        assert isinstance(all_monitor_data["sys1"], MonitorData)
        assert all_monitor_data["sys1"].monetary == "USD"
        assert isinstance(all_monitor_data["sys2"], MonitorData)
        assert all_monitor_data["sys2"].monetary == "EUR"

def test_get_data_token_expired_and_renewed(hypon_client, mock_config):
    hypon_client.token = "expired_token"
    system_ids = ["sys1"]

    with patch('requests.get') as mock_get, \
         patch.object(hypon_client, 'login', side_effect=lambda config: setattr(hypon_client, 'token', "new_token") or "new_token") as mock_login:

        # First call to get_data for sys1 - simulates 401 (token expired)
        mock_response_401 = MagicMock()
        mock_response_401.status_code = 401
        mock_response_401.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response_401)

        # Second call to get_data for sys1 after re-login - simulates success
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"code": 20000, "data": {"monetary": "USD", "today_earning": 10.0, "month_earning": 100.0, "total_earning": 1000.0, "e_total": 5000.0, "e_month": 500.0, "e_today": 50.0, "e_year": 2000.0, "total_tree": 5, "total_co2": 10, "total_diesel": 20, "percent": 90.0, "meter_power": 5.0, "power_load": 2.0, "w_cha": 1.0, "power_pv": 3.0, "soc": 80.0, "micro": 0.5}}

        mock_get.side_effect = [mock_response_401, mock_response_success]

        all_monitor_data = hypon_client.get_data(mock_config, system_ids)

        mock_login.assert_called_once_with(mock_config)
        assert hypon_client.token == "new_token"
        assert len(all_monitor_data) == 1
        assert isinstance(all_monitor_data["sys1"], MonitorData)
        assert all_monitor_data["sys1"].monetary == "USD"

def test_get_data_request_exception(hypon_client, mock_config):
    hypon_client.token = "existing_token"
    system_ids = ["sys1"]
    with patch('requests.get', side_effect=requests.exceptions.RequestException("Network error")):
        all_monitor_data = hypon_client.get_data(mock_config, system_ids)

        assert len(all_monitor_data) == 1
        assert all_monitor_data["sys1"] is None

def test_get_data_no_token_initially(hypon_client, mock_config):
    hypon_client.token = None
    system_ids = ["sys1"]

    with (patch.object(hypon_client, 'login', side_effect=lambda config: setattr(hypon_client, 'token', "new_token") or "new_token") as mock_login,
          patch('requests.get') as mock_get):
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"code": 20000, "data": {"monetary": "USD", "today_earning": 10.0, "month_earning": 100.0, "total_earning": 1000.0, "e_total": 5000.0, "e_month": 500.0, "e_today": 50.0, "e_year": 2000.0, "total_tree": 5, "total_co2": 10, "total_diesel": 20, "percent": 90.0, "meter_power": 5.0, "power_load": 2.0, "w_cha": 1.0, "power_pv": 3.0, "soc": 80.0, "micro": 0.5}}
        mock_get.return_value = mock_response_success

        all_monitor_data = hypon_client.get_data(mock_config, system_ids)

        mock_login.assert_called_once_with(mock_config)
        assert hypon_client.token == "new_token"
        assert len(all_monitor_data) == 1
        assert isinstance(all_monitor_data["sys1"], MonitorData)

def test_get_data_login_fails_initially(hypon_client, mock_config):
    hypon_client.token = None
    system_ids = ["sys1"]

    with patch.object(hypon_client, 'login', return_value=None) as mock_login:
        all_monitor_data = hypon_client.get_data(mock_config, system_ids)

        mock_login.assert_called_once_with(mock_config)
        assert hypon_client.token is None
        assert len(all_monitor_data) == 0 # No data fetched if login fails
