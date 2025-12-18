#!/usr/bin/env python3
import os
import subprocess
import sys
import time


def run_command(command, env=None):
    """Run a shell command and return the exit code."""
    print(f"Running: {' '.join(command)}")
    return subprocess.run(command, env=env).returncode


def main():
    # 1. Start Docker services
    print("Starting Docker services (mosquitto and wiremock)...")
    docker_cmd = ["docker", "compose", "-f", "docker-compose.dev.yml", "up", "mosquitto", "wiremock", "-d"]
    if run_command(docker_cmd) != 0:
        print("Error starting Docker services.")
        sys.exit(1)

    # 2. Wait for services to be ready
    print("Waiting for WireMock to be healthy...")
    # WireMock has a healthcheck in docker-compose.dev.yml
    # We can wait a bit or use docker inspect to check health
    for _ in range(30):
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Health.Status}}", "wiremock"],
            capture_output=True, text=True
        )
        if result.stdout.strip() == "healthy":
            print("WireMock is healthy!")
            break
        time.sleep(1)
    else:
        print("Timeout waiting for WireMock to be healthy.")
        # Proceed anyway, maybe it just takes time

    # 3. Set environment variables for the test
    test_env = os.environ.copy()
    test_env["HTTP_URL"] = "http://localhost:8080"
    test_env["SYSTEM_IDS"] = "your_system_id_1"
    test_env["API_USERNAME"] = "test_user"
    test_env["API_PASSWORD"] = "test_password"
    test_env["MQTT_BROKER"] = "localhost"
    test_env["MQTT_PORT"] = "1883"

    # 4. Run pytest
    print("Running integration tests...")

    # Try to find the python executable in the venv
    if os.name == "nt":  # Windows
        python_exe = os.path.join(".venv", "Scripts", "python.exe")
    else:
        python_exe = os.path.join(".venv", "bin", "python")

    if not os.path.exists(python_exe):
        python_exe = sys.executable  # Fallback to current python
        print(f"Warning: Virtual environment not found at .venv, using {python_exe}")

    pytest_cmd = [python_exe, "-m", "pytest", "tests/test_wiremock_integration.py"]

    exit_code = run_command(pytest_cmd, env=test_env)

    # 5. Cleanup
    print("Cleaning up Docker services...")
    run_command(["docker", "compose", "-f", "docker-compose.dev.yml", "stop", "mosquitto", "wiremock"])

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
