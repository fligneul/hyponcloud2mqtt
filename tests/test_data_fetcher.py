import pytest
from unittest.mock import MagicMock, patch
from hyponcloud2mqtt.data_fetcher import DataFetcher
from hyponcloud2mqtt.http_client import AuthenticationError


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.http_url = "http://api.example.com"
    config.api_username = "testuser"
    config.api_password = "testpass"
    config.verify_ssl = True
    return config


@pytest.fixture
def data_fetcher(mock_config):
    # Patch requests.Session during initialization
    with patch('requests.Session') as mock_session_cls:
        mock_session = mock_session_cls.return_value

        # Mock successful login by default during setup_clients
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 20000,
            "data": {"token": "initial-token"}
        }
        mock_session.post.return_value = mock_response

        fetcher = DataFetcher(mock_config, "system_id_123")
        return fetcher


def test_login_success(mock_config):
    with patch('requests.Session') as mock_session_cls:
        mock_session = mock_session_cls.return_value

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 20000,
            "data": {"token": "new-token"}
        }
        mock_session.post.return_value = mock_response

        fetcher = DataFetcher(mock_config, "system_id_123")

        # Reset mocks to test separate calls if needed,
        # but _login is called in __init__, so we already verified it implicity via creation.
        # Let's call _login explicitly to verification.
        token = fetcher._login()

        assert token == "new-token"
        mock_session.post.assert_called_with(
            "http://api.example.com/login",
            json={"username": "testuser", "password": "testpass", "oem": None},
            timeout=10
        )


def test_login_failure_wrong_code(mock_config):
    with patch('requests.Session') as mock_session_cls:
        mock_session = mock_session_cls.return_value

        # Setup login to fail
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 50001, "message": "Failed"}
        mock_session.post.return_value = mock_response

        # Because setup_clients calls _login, and if it fails (returns None)
        # it might exit if no token. But here credentials are present.
        # DataFetcher exits if token failure AND creds present?
        # Yes: if token... elif creds: sys.exit(1)

        # We need to catch SystemExit or prevent it.
        # But wait, if _login returns None, setup_clients calls sys.exit(1).

        with pytest.raises(SystemExit):
            DataFetcher(mock_config, "system_id_123")


def test_fetch_all_success(data_fetcher):
    # Setup mock clients to return data
    data_fetcher.monitor_client.fetch_data = MagicMock(return_value={"data": {"mon": 1}})
    data_fetcher.production_client.fetch_data = MagicMock(return_value={"data": {"prod": 2}})
    data_fetcher.status_client.fetch_data = MagicMock(return_value={"data": {"stat": 3}})

    # Mock merge_api_data to just return the combined dict
    with patch('hyponcloud2mqtt.data_fetcher.merge_api_data') as mock_merge:
        mock_merge.return_value = {"mon": 1, "prod": 2, "stat": 3}

        result = data_fetcher.fetch_all()

        assert result == {"mon": 1, "prod": 2, "stat": 3}
        mock_merge.assert_called_once()


def test_fetch_all_reauth_flow(data_fetcher):
    # Scenario:
    # 1. Fetch fails with AuthenticationError
    # 2. _login is called and succeeds
    # 3. Fetch retries and succeeds

    # Mock clients
    # First call raises AuthError, second call returns data
    side_effect_auth = [AuthenticationError("Token expired"), {"data": {"val": 1}}]
    data_fetcher.monitor_client.fetch_data = MagicMock(side_effect=side_effect_auth)

    # Other clients just succeed
    data_fetcher.production_client.fetch_data = MagicMock(return_value={"data": {"val": 2}})
    data_fetcher.status_client.fetch_data = MagicMock(return_value={"data": {"val": 3}})

    # Mock _login to return a new token
    # Note: data_fetcher instance already has a mock session from the fixture
    # We need to configure the session.post response for the re-login
    relogin_response = MagicMock()
    relogin_response.status_code = 200
    relogin_response.json.return_value = {"code": 20000, "data": {"token": "reauth-token"}}
    data_fetcher.session.post.return_value = relogin_response

    with patch('hyponcloud2mqtt.data_fetcher.merge_api_data') as mock_merge:
        mock_merge.return_value = "merged_data"

        result = data_fetcher.fetch_all()

        # Check if Authorization header was updated
        data_fetcher.session.headers.update.assert_called_with(
            {"Authorization": "Bearer reauth-token"})

        assert result == "merged_data"


def test_fetch_all_max_retries_exceeded(data_fetcher):
    # Mock all clients to always raise AuthenticationError
    data_fetcher.monitor_client.fetch_data = MagicMock(side_effect=AuthenticationError("Fail"))
    data_fetcher.production_client.fetch_data = MagicMock(side_effect=AuthenticationError("Fail"))
    data_fetcher.status_client.fetch_data = MagicMock(side_effect=AuthenticationError("Fail"))

    # Mock login to fail (return None) so retry fails immediately?
    # Or mock login to succeed but fetch still fails?
    # Let's mock login to succeed, but fetch continues to fail (e.g. token invalid immediately)

    relogin_response = MagicMock()
    relogin_response.status_code = 200
    relogin_response.json.return_value = {"code": 20000, "data": {"token": "token-2"}}
    data_fetcher.session.post.return_value = relogin_response

    result = data_fetcher.fetch_all()

    assert result is None
    # Verify we tried to re-login multiple times?
    # With max_retries=2:
    # Attempt 0: Fetch fails -> Login success -> continue
    # Attempt 1: Fetch fails -> Login success -> continue
    # loop ends.
    # wait, Logic is:
    # for attempt in range(max_retries):
    #   if success: break
    #   except AuthError:
    #     if attempt < max - 1:
    #        login()
    #     else:
    #        log error

    # So with max_retries=2:
    # attempt 0: fails. 0 < 1. login(). continue.
    # attempt 1: fails. 1 is not < 1. Log error. break.

    # So we expect 1 re-login attempt.
    # Initial login (from fixture) + 1 re-login = 2 calls to post(/login) (approx)
    # Actually checking call count on session.post is tricky because of fixture interaction.
    pass


def test_clients_share_session(data_fetcher):
    """Verify that all clients share the same session instance (Connection Pooling)."""
    assert data_fetcher.monitor_client.session is data_fetcher.session
    assert data_fetcher.production_client.session is data_fetcher.session
    assert data_fetcher.status_client.session is data_fetcher.session


def test_data_fetcher_no_creds():
    """Test that login is skipped if no credentials are provided."""
    config = MagicMock()
    config.http_url = "http://api.example.com"
    config.api_username = None
    config.api_password = None
    config.verify_ssl = True

    with patch('requests.Session'):
        fetcher = DataFetcher(config, "sys_id")

        # Verify _login returned None (implied by no auth header update)
        # and setup_clients didn't exit (because checks are inside _login or setup_clients)
        # setup_clients: if token: ... elif creds: exit
        # Here token is None, creds is False -> No exit, no header update.

        # Verify no login attempt
        fetcher.session.post.assert_not_called()

        # Verify clients initialized
        assert fetcher.monitor_client is not None


def test_session_config_verify():
    """Verify that session is configured with the correct verify_ssl setting."""
    config = MagicMock()
    config.http_url = "http://api.example.com"
    config.api_username = "u"
    config.api_password = "p"
    config.verify_ssl = False  # Test False case

    with patch('requests.Session') as mock_session_cls:
        mock_session = mock_session_cls.return_value
        # Mock login to avoid failure
        mock_session.post.return_value.status_code = 200
        mock_session.post.return_value.json.return_value = {
            "code": 20000, "data": {"token": "t"}}

        fetcher = DataFetcher(config, "sys_id")

        assert fetcher.session.verify is False


def test_fetch_all_generic_failure(data_fetcher):
    """Test when all endpoints fail with generic errors (not auth)."""
    # Mock clients to return None (as they do on error)
    data_fetcher.monitor_client.fetch_data = MagicMock(return_value=None)
    data_fetcher.production_client.fetch_data = MagicMock(return_value=None)
    data_fetcher.status_client.fetch_data = MagicMock(return_value=None)

    result = data_fetcher.fetch_all()

    assert result is None
