"""Hypon API client module."""

from dataclasses import dataclass
import logging
from typing import Dict, List
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HyponAPIError(Exception):
    """Custom exception for Hypon API errors."""


class HyponAuthenticationError(HyponAPIError):
    """Custom exception for authentication errors."""


class HyponRequestError(HyponAPIError):
    """Custom exception for request errors."""


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

    def __init__(self, config: Dict):
        self.config = config.get("hypon", {})
        self.token = None

    def login(self) -> None:
        """Logs in to the Hypon API and sets the token."""
        payload = {
            "username": self.config.get("user"),
            "password": self.config.get("password"),
            "oem": None,
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
        }
        try:
            response = requests.post(
                f"{self.config.get('api_base_url')}/login",
                json=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
            response_json = response.json()
            if response_json.get("code") != 20000:
                raise HyponAuthenticationError(
                    f"Login failed: {response_json.get('message')}"
                )

            self.token = response_json.get("data", {}).get("token")
            if not self.token:
                raise HyponAuthenticationError("Login failed: No token received.")

            logger.info("Successfully logged in to Hypon API.")
        except requests.exceptions.RequestException as e:
            raise HyponRequestError(f"Error during login request: {e}") from e

    def get_data(
        self, system_ids: List[str], retries: int = 0
    ) -> Dict[str, MonitorData]:
        """
        Fetches data from the Hypon API for multiple system IDs with configurable retry logic.

        Args:
            system_ids: A list of system IDs to fetch data for.
            retries: The number of times to retry fetching data for a system ID if it fails.
                     Defaults to 0 (no retries).
        """
        if not self.token:
            try:
                self.login()
            except (HyponAuthenticationError, HyponRequestError) as e:
                logger.error("Initial login failed: %s", e)
                return {}

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
        }

        all_monitor_data = {}
        for system_id in system_ids:
            data_url = f"{self.config.get('api_base_url')}/plant/{system_id}/monitor?refresh=true"

            for attempt in range(retries + 1):
                try:
                    response = requests.get(data_url, headers=headers, timeout=30)
                    response.raise_for_status()
                    response_json = response.json()
                    if response_json.get("code") == 20000:
                        monitor_data = MonitorData(**response_json.get("data", {}))
                        all_monitor_data[system_id] = monitor_data
                        break  # Success, break the retry loop
                    else:
                        raise HyponAPIError(
                            f"API error for system ID {system_id}: {response_json.get('message')}"
                        )
                except requests.exceptions.RequestException as e:
                    logger.error(
                        "Request exception for system ID %s (Attempt %s/%s): %s",
                        system_id,
                        attempt + 1,
                        retries + 1,
                        e,
                    )
                    if attempt < retries:
                        logger.info(
                            "Retrying... (Attempt %s/%s)", attempt + 2, retries + 1
                        )
                    else:
                        logger.error(
                            "Failed to get data for system ID %s after %s attempts.",
                            system_id,
                            retries + 1,
                        )
                        all_monitor_data[system_id] = None
                except HyponAPIError as e:
                    logger.error(
                        "API error for system ID %s (Attempt %s/%s): %s",
                        system_id,
                        attempt + 1,
                        retries + 1,
                        e,
                    )
                    if attempt < retries:
                        logger.info(
                            "Retrying login and data fetch... (Attempt %s/%s)",
                            attempt + 2,
                            retries + 1,
                        )
                        try:
                            self.login()
                            headers["Authorization"] = f"Bearer {self.token}"
                        except (HyponAuthenticationError, HyponRequestError) as login_e:
                            logger.error(
                                "Re-login failed: %s. Aborting retries for this system.",
                                login_e,
                            )
                            all_monitor_data[system_id] = None
                            break
                    else:
                        logger.error(
                            "Failed to get data for system ID %s after %s attempts.",
                            system_id,
                            retries + 1,
                        )
                        all_monitor_data[system_id] = None

        return all_monitor_data
