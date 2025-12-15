import logging
import sys
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from .http_client import HttpClient, AuthenticationError
from .data_merger import merge_api_data

logger = logging.getLogger(__name__)


class DataFetcher:
    def __init__(self, config, system_id: str):
        self.config = config
        self.system_id = system_id
        self.base_url = config.http_url.rstrip('/')
        self.session = requests.Session()
        self.session.verify = self.config.verify_ssl
        self.monitor_client = None
        self.production_client = None
        self.status_client = None
        self._reauth_lock = threading.Lock()

        self.setup_clients()

    def _login(self) -> str | None:
        """
        Login to the API and retrieve Bearer token.
        """
        if not (self.config.api_username and self.config.api_password):
            logger.warning("No API credentials provided, skipping login")
            return None

        login_url = f"{self.base_url}/login"
        logger.info(f"Attempting login to {login_url}")
        payload = {
            "username": self.config.api_username,
            "password": self.config.api_password,
            "oem": None
        }

        try:
            response = self.session.post(login_url, json=payload, timeout=10)
            logger.debug(
                f"Login request sent, status code: {response.status_code}")
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, dict):
                logger.error(f"Login response is not a JSON object: {data}")
                return None

            code = data.get("code")
            if code != 20000:
                logger.error(f"Login failed with code {code}")
                return None

            token = data.get("data", {}).get("token")
            if not token:
                logger.error("No token in login response")
                return None

            logger.info("Successfully logged in and retrieved token")
            return token

        except requests.RequestException as e:
            logger.error(f"Error during login: {e}")
            return None
        except ValueError as e:
            logger.error(f"Error parsing login response: {e}")
            return None

    def setup_clients(self):
        # Login to get Bearer token
        token = self._login()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        elif self.config.api_username and self.config.api_password:
            # If login was expected but failed
            logger.critical("Failed to retrieve Bearer token")
            sys.exit(1)

        # Construct plant-specific base URL
        plant_base_url = f"{self.base_url}/plant/{self.system_id}"

        self.monitor_client = HttpClient(
            f"{plant_base_url}/monitor?refresh=true", self.session)
        self.production_client = HttpClient(
            f"{plant_base_url}/production2", self.session)
        self.status_client = HttpClient(
            f"{plant_base_url}/status", self.session)

        logger.info("HTTP clients initialized for 3 endpoints")

    def fetch_all(self):
        monitor_data = None
        production_data = None
        status_data = None

        # Retry loop for authentication handling
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Fetch from all 3 endpoints in parallel
                with ThreadPoolExecutor(max_workers=3) as executor:
                    future_monitor = executor.submit(
                        self.monitor_client.fetch_data)
                    future_production = executor.submit(
                        self.production_client.fetch_data)
                    future_status = executor.submit(
                        self.status_client.fetch_data)

                    # Wait for all futures to complete
                    futures = [
                        future_monitor,
                        future_production,
                        future_status]

                    # Check for exceptions in futures
                    for future in as_completed(futures):
                        future.result()  # This will raise AuthenticationError if present

                    # If no exception, get results
                    monitor_data = future_monitor.result()
                    production_data = future_production.result()
                    status_data = future_status.result()

                # If we got here, all requests succeeded
                break

            except AuthenticationError:
                logger.warning(
                    f"Authentication failed during fetch (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    # Use a lock to prevent multiple threads from trying to re-login at once
                    with self._reauth_lock:
                        logger.info("Attempting to re-login...")
                        new_token = self._login()
                        if new_token:
                            logger.info(
                                "Successfully re-authenticated, updating session token")
                            self.session.headers.update(
                                {"Authorization": f"Bearer {new_token}"})
                            continue  # Retry the loop
                        else:
                            logger.error("Re-authentication failed")
                            break  # Stop retrying
                else:
                    logger.error("Max retries reached for authentication")
            except Exception as e:
                logger.error(f"Unexpected error during fetch: {e}")
                break

        # Check if all requests failed
        if monitor_data is None and production_data is None and status_data is None:
            logger.warning("All API requests failed or returned None")
            return None

        # Merge data
        return merge_api_data(monitor_data, production_data, status_data)
