import os
import pytest


def test_print_env():
    print("\n=== DEBUG TEST ENV DUMP ===")
    for k, v in sorted(os.environ.items()):
        if k in ["HTTP_URL", "MQTT_BROKER", "MQTT_PORT"]:
            print(f"{k}={v}")
    print("===========================")

    # Assert that HTTP_URL is present, or fail explicitly
    if "HTTP_URL" not in os.environ:
        pytest.fail("HTTP_URL environment variable is MISSING in pytest execution!")

    assert os.environ["HTTP_URL"] == "http://127.0.0.1:8080"
