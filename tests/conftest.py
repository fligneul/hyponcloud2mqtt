from __future__ import annotations
import os
import pytest

@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    """
    Override the default docker_compose_file fixture to specify the path
    to the test-specific docker-compose.yml.
    """
    return "tests/docker-compose.yml"

@pytest.fixture(scope="session")
def integration_services(docker_ip, docker_services):
    """
    A session-scoped fixture that spins up the WireMock and Mosquitto services
    using pytest-docker. It waits for the services to be healthy and makes
    their connection details available to the tests by setting environment
    variables. The services are automatically torn down at the end of the
    test session.
    """
    # Get the mapped ports for the services
    wiremock_port = docker_services.port_for("wiremock", 8080)
    mqtt_port = docker_services.port_for("mosquitto", 1883)

    # Get the IP address of the Docker host
    host = docker_ip

    # Set the environment variables
    os.environ["WIREMOCK_HOST"] = host
    os.environ["WIREMOCK_PORT"] = str(wiremock_port)
    os.environ["MQTT_BROKER_HOST"] = host
    os.environ["MQTT_BROKER_PORT"] = str(mqtt_port)

    # The docker_ip and docker_services fixtures are provided by pytest-docker.
    # docker_services will automatically wait for the healthchecks to pass.

    # You can add additional checks here if needed, for example, to wait
    # for a specific log message from a service.

    # The fixture doesn't need to return anything, as its primary purpose
    # is to manage the lifecycle of the services. Tests that use this
    # fixture will run after the services are up and healthy.
    yield
