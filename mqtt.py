import paho.mqtt.client as mqtt


MQTT_TOPICS = []


def append_topic(topic):
    MQTT_TOPICS.append(topic)


def add_topic_callback(mqttc, topic, cb):
    mqttc.subscribe(topic)
    MQTT_TOPICS.append(topic)

    mqttc.message_callback_add(topic, cb)


def on_connect(mqttc, _userdata, _flags, rc):
    print("MQTT client connected with code %s" % rc)

    for topic in MQTT_TOPICS:
        mqttc.subscribe(topic)


def on_disconnect(mqttc, _userdata, rc):
    print("MQTT client disconnected with code %s" % rc)


def create_client(config):
    if "host" not in config:
        raise ValueError("Missing MQTT host configuration! See template for an example.")

    host = config.get("host")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    try:
        client.connect(host, 1883, 60)
    except ConnectionRefusedError as e:
        print(f"Failed to connect to MQTT client, will try again: %s" % e)

    client.loop_start()

    return client
