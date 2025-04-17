import paho.mqtt.client as mqtt
import util
import logging

class MqttConfig:
    @staticmethod
    def from_env(env_prefix=""):
        host = util.load_env(env_prefix+"HOST")
        if host is None:
            raise KeyError("Missing HOST configuration for MQTT")

        prefix = util.load_env(env_prefix+"PREFIX")

        return MqttConfig(host, prefix)

    def __init__(self, host, prefix=None):
        self._host = host
        self._prefix = prefix

    @property
    def host(self):
        return self._host

    @property
    def prefix(self):
        return self._prefix

    def __str__(self):
        return f"MqttConfig(host={self._host}, prefix={self._prefix})"


MQTT_TOPICS = []


def append_topic(topic):
    MQTT_TOPICS.append(topic)


def add_topic_callback(mqttc, topic, cb):
    mqttc.subscribe(topic)
    MQTT_TOPICS.append(topic)

    mqttc.message_callback_add(topic, cb)


def on_connect(mqttc, _userdata, _flags, rc):
    logging.info("MQTT client connected with code %s", rc)

    for topic in MQTT_TOPICS:
        mqttc.subscribe(topic)


def on_disconnect(mqttc, _userdata, rc):
    logging.info("MQTT client disconnected with code %s",rc)


def create_client(mqtt_config):
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    try:
        client.connect(mqtt_config.host, 1883, 60)
    except ConnectionRefusedError as e:
        logging.error(f"Failed to connect to MQTT client, will try again: %s", e)

    client.loop_start()

    return client
