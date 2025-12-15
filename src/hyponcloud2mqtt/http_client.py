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
            session: requests.Session):
        self.url = url
        self.session = session
        logger.debug(f"Initialized HttpClient for {url}")

    def fetch_data(self) -> Any | None:
        logger.debug(f"Fetching data from {self.url}")
        try:
            response = self.session.get(self.url, timeout=10)
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
            # SSL verification is now handled by the session, but it's good to keep this logging
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
