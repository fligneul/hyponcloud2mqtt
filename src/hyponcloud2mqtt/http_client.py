from __future__ import annotations
import requests
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when API authentication fails (code 50008)."""


class HttpClient:
    def __init__(
            self,
            url: str,
            token: str | None = None,
            verify_ssl: bool = True):
        self.url = url
        self.token = token
        self.verify_ssl = verify_ssl
        logger.debug(
            f"Initialized HttpClient for {url} (SSL verification: {verify_ssl})")

    @staticmethod
    def login(
            base_url: str,
            username: str,
            password: str,
            verify_ssl: bool = True) -> str | None:
        """
        Login to the API and retrieve Bearer token.

        Args:
            base_url: Base URL of the API
            username: API username
            password: API password
            verify_ssl: Whether to verify SSL certificates

        Returns:
            Bearer token or None if login failed
        """
        login_url = f"{base_url.rstrip('/')}/login"
        logger.info(f"Attempting login to {login_url}")
        payload = {
            "username": username,
            "password": password,
            "oem": None
        }

        try:
            response = requests.post(
                login_url, json=payload, timeout=10, verify=verify_ssl)
            logger.debug(
                f"Login request sent, status code: {response.status_code}")
            response.raise_for_status()
            data = response.json()

            # Validate response
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

    def update_token(self, token: str):
        """Update the Bearer token for this client."""
        self.token = token

    def fetch_data(self) -> Any | None:
        logger.debug(f"Fetching data from {self.url}")
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            response = requests.get(
                self.url, headers=headers, timeout=10, verify=self.verify_ssl)
            logger.debug(
                f"Response received from {self.url}, status code: {response.status_code}")
            response.raise_for_status()
            data = response.json()

            # Validate custom code field
            if not isinstance(data, dict):
                logger.error(f"Response is not a JSON object: {data}")
                return None

            code = data.get("code")

            # Check for authentication failure
            if code == 50008:
                logger.warning(
                    f"Authentication failed (code 50008) for {self.url} - token may be expired")
                raise AuthenticationError(
                    "Token expired or invalid (code 50008)")

            if code != 20000:
                logger.error(f"API returned error code {code} from {self.url}")
                return None

            logger.debug(f"Successfully fetched data from {self.url}")
            return data
        except requests.exceptions.SSLError as e:
            logger.error(
                f"SSL certificate verification failed for {self.url}: {e}")
            logger.error(
                "Consider setting VERIFY_SSL=false if using self-signed certificates")
            return None
        except requests.RequestException as e:
            logger.error(f"Error fetching data from {self.url}: {e}")
            return None
        except ValueError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return None
