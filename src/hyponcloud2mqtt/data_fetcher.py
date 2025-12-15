import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from .http_client import HttpClient, AuthenticationError
from .data_merger import merge_api_data

logger = logging.getLogger(__name__)


class DataFetcher:
    def __init__(self, config, system_id: str, http_client: HttpClient = None):
        self.config = config
        self.system_id = system_id
        self.base_url = config.http_url.rstrip('/')
        self.token = None
        self.monitor_client = None
        self.production_client = None
        self.status_client = None
        self.http_client = http_client

        self.setup_clients()

    def setup_clients(self):
        if self.http_client:
            self.monitor_client = self.http_client
            self.production_client = self.http_client
            self.status_client = self.http_client
            return
        # Login to get Bearer token
        if self.config.api_username and self.config.api_password:
            logger.info("Logging in to retrieve Bearer token...")
            self.token = HttpClient.login(
                self.base_url,
                self.config.api_username,
                self.config.api_password,
                self.config.verify_ssl)
            if not self.token:
                logger.critical("Failed to retrieve Bearer token")
                sys.exit(1)
            logger.info("Successfully authenticated")
        else:
            logger.warning("No API credentials provided")

        # Construct plant-specific base URL
        plant_base_url = f"{self.base_url}/plant/{self.system_id}"

        self.monitor_client = HttpClient(
            f"{plant_base_url}/monitor?refresh=true",
            self.token,
            self.config.verify_ssl)
        self.production_client = HttpClient(
            f"{plant_base_url}/production2", self.token, self.config.verify_ssl)
        self.status_client = HttpClient(
            f"{plant_base_url}/status", self.token, self.config.verify_ssl)

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

                # If we got here, all requests succeeded (or failed without
                # AuthError)
                break

            except AuthenticationError:
                logger.warning(
                    f"Authentication failed during fetch (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    if self.config.api_username and self.config.api_password:
                        logger.info("Attempting to re-login...")
                        new_token = HttpClient.login(
                            self.base_url,
                            self.config.api_username,
                            self.config.api_password,
                            self.config.verify_ssl)
                        if new_token:
                            logger.info(
                                "Successfully re-authenticated, updating tokens")
                            self.monitor_client.update_token(new_token)
                            self.production_client.update_token(new_token)
                            self.status_client.update_token(new_token)
                            continue  # Retry the loop
                        else:
                            logger.error("Re-authentication failed")
                            break  # Stop retrying
                    else:
                        logger.error("No credentials to re-authenticate")
                        break
                else:
                    logger.error("Max retries reached for authentication")
            except Exception as e:
                logger.error(f"Unexpected error during fetch: {e}")
                break

        # Check if all requests failed (general failure, not caught by
        # AuthError logic)
        if monitor_data is None and production_data is None and status_data is None:
            logger.warning("All API requests failed or returned None")
            return None

        # Merge data
        return merge_api_data(monitor_data, production_data, status_data)
