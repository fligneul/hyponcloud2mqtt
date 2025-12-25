from unittest.mock import MagicMock
from hyponcloud2mqtt.mqtt_client import MqttClient


def test_publish_with_retain():
    """Test that publish method accepts and passes retain argument."""
    # Arrange
    client = MqttClient(
        broker="localhost",
        port=1883,
        topic="test/topic",
        availability_topic="test/status",
        dry_run=False
    )
    mock_paho_client = MagicMock()
    client.client = mock_paho_client

    data = {"key": "value"}
    topic = "specific/topic"

    # Act
    client.publish(data, topic=topic, retain=True)

    # Assert
    mock_paho_client.publish.assert_called_once()
    args, kwargs = mock_paho_client.publish.call_args
    assert args[0] == topic
    assert kwargs['retain'] is True


def test_publish_default_retain():
    """Test that publish method defaults retain to False."""
    # Arrange
    client = MqttClient(
        broker="localhost",
        port=1883,
        topic="test/topic",
        availability_topic="test/status",
        dry_run=False
    )
    mock_paho_client = MagicMock()
    client.client = mock_paho_client

    data = {"key": "value"}

    # Act
    client.publish(data)

    # Assert
    mock_paho_client.publish.assert_called_once()
    _, kwargs = mock_paho_client.publish.call_args
    assert kwargs['retain'] is False
