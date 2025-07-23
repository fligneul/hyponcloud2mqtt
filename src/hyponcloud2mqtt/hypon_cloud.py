"""Hypon API client module."""
from dataclasses import dataclass
import requests

@dataclass
class MonitorData:
    """Represents the data returned by the Hypon monitor API."""
    # pylint: disable=too-many-instance-attributes
    monetary: str
    today_earning: float
    month_earning: float
    total_earning: float
    e_total: float
    e_month: float
    e_today: float
    e_year: float
    total_tree: float
    total_co2: float
    total_diesel: float
    percent: float
    meter_power: float
    power_load: float
    w_cha: float
    power_pv: float
    soc: float
    micro: float

class HyponCloudClient:
    """Client for interacting with the Hypon Cloud API."""
    def __init__(self):
        self.token = None

    def login(self, config):
        """Logs in to the Hypon API and returns a token."""
        hypon_config = config.get("hypon", {})
        payload = {'username': hypon_config.get("user"), 'password': hypon_config.get("password"), 'oem': None}
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
        }
        try:
            response = requests.post(f"{hypon_config.get('api_base_url')}/login", json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            response_json = response.json()
            if response_json.get("code") != 20000:
                print(f"Error logging in: {response_json.get('message')}")
                return None
            self.token = response_json.get("data", {}).get("token")
            return self.token
        except requests.exceptions.RequestException as e:
            print(f"Error logging in: {e}")
            return None

    def get_data(self, config, system_ids):
        """Fetches data from the Hypon API for multiple system IDs."""
        hypon_config = config.get("hypon", {})
        if not self.token:
            self.login(config)

        if not self.token:
            return {}

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
        }

        all_monitor_data = {}
        for system_id in system_ids:
            data_url = f"{hypon_config.get('api_base_url')}/plant/{system_id}/monitor?refresh=true"
            try:
                response = requests.get(data_url, headers=headers, timeout=30)
                response.raise_for_status()
                response_json = response.json()
                if response_json.get("code") != 20000:
                    print(f"Error getting data for system ID {system_id}: {response_json.get('message')}")
                    all_monitor_data[system_id] = None
                    continue
                monitor_data = MonitorData(**response_json.get("data", {}))
                all_monitor_data[system_id] = monitor_data

            except requests.exceptions.RequestException as e:
                print(f"Error getting data for system ID {system_id}: {e}")
                # If token is expired, login again and retry
                if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 401:
                    print("Token expired, renewing...")
                    self.login(config)
                    # After re-login, retry the current system_id
                    if self.token:
                        try:
                            response = requests.get(data_url, headers=headers, timeout=30)
                            response.raise_for_status()
                            response_json = response.json()
                            if response_json.get("code") != 20000:
                                print(f"Error getting data for system ID {system_id} after re-login: "
                                      f"{response_json.get('message')}")
                                all_monitor_data[system_id] = None
                                continue
                            monitor_data = MonitorData(**response_json.get("data", {}))
                            all_monitor_data[system_id] = monitor_data
                        except requests.exceptions.RequestException as retry_e:
                            print(f"Error getting data for system ID {system_id} after re-login retry: "
                                      f"{retry_e}")
                            all_monitor_data[system_id] = None
                    else:
                        all_monitor_data[system_id] = None
                else:
                    all_monitor_data[system_id] = None
        return all_monitor_data

