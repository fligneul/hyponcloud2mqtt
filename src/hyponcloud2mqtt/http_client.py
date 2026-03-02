from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when API authentication fails (code 50008)."""


class HttpClient:
    def __init__(self, url: str, client: httpx.Client):
        self.url = url
        self.client = client
        logger.debug("Initialized HttpClient for %s", url)

    def fetch_data(self) -> Any | None:
        logger.debug("Fetching data from %s", self.url)
        try:
            response = self.client.get(self.url, timeout=10)
            logger.debug("Response received from %s, status code: %s", self.url, response.status_code)
            response.raise_for_status()
            data = response.json()

            # Validate custom code field
            if not isinstance(data, dict):
                logger.error("Response is not a JSON object: %s", data)
                return None

            code = data.get("code")

            # Check for authentication failure
            if code == 50008:
                logger.warning("Authentication failed (code 50008) for %s - token may be expired", self.url)
                raise AuthenticationError("Token expired or invalid (code 50008)")

            if code != 20000:
                logger.error("API returned error code %s from %s", code, self.url)
                return None

            logger.debug("Successfully fetched data from %s", self.url)
            return data
        except httpx.ConnectError as e:
            logger.error("SSL/connection error for %s: %s", self.url, e)
            logger.error("Consider setting VERIFY_SSL=false if using self-signed certificates")
            return None
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error fetching data from %s: %s", self.url, e)
            return None
        except httpx.HTTPError as e:
            logger.error("Error fetching data from %s: %s", self.url, e)
            return None
        except ValueError as e:
            logger.error("Error parsing JSON response: %s", e)
            return None
