from hyponcloud2mqtt.mqtt_client import MqttClient


def test_on_connect_not_authorized_tip(caplog):
    """Test that 'Not authorized' reason code includes troubleshooting tip."""
    client = MqttClient(
        broker="localhost",
        port=1883,
        topic="test",
        availability_topic="test/status"
    )

    # ReasonCode-like object for MQTT v3.1.1 (5 = Not authorized)
    rc = 5

    with caplog.at_level("ERROR"):
        client._on_connect(None, None, None, rc)

    assert "Failed to connect to MQTT broker, reason: 5" in caplog.text
    assert "[TIP] 'Not authorized' typically means" in caplog.text
    assert "Incorrect MQTT_USERNAME or MQTT_PASSWORD" in caplog.text


def test_on_connect_bad_credentials_tip(caplog):
    """Test that 'Bad user name or password' reason code includes troubleshooting tip."""
    client = MqttClient(
        broker="localhost",
        port=1883,
        topic="test",
        availability_topic="test/status"
    )

    # ReasonCode-like object for MQTT v3.1.1 (4 = Bad user name or password)
    rc = 4

    with caplog.at_level("ERROR"):
        client._on_connect(None, None, None, rc)

    assert "Failed to connect to MQTT broker, reason: 4" in caplog.text
    assert "Double-check MQTT_USERNAME and MQTT_PASSWORD" in caplog.text


def test_on_connect_connection_refused_tip(caplog):
    """Test that 'Connection refused' reason code includes troubleshooting tip."""
    client = MqttClient(
        broker="localhost",
        port=1883,
        topic="test",
        availability_topic="test/status"
    )

    # Mocking rc as a string which sometimes happens with Paho's string representation
    rc = "Connection refused"

    with caplog.at_level("ERROR"):
        client._on_connect(None, None, None, rc)

    assert "Failed to connect to MQTT broker, reason: Connection refused" in caplog.text
    assert "Check MQTT_BROKER address, MQTT_PORT, and firewall settings" in caplog.text
