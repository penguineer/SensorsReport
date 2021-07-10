#!/usr/bin/env python3

# Author: Stefan Haun <tux@netz39.de>

import signal
import sys
import json
import time

import mqtt

import sensors

import util

running = True


def sigint_handler(_signal, _frame):
    global running

    if running:
        print("SIGINT received. Stopping the queue.")
        running = False
    else:
        print("Receiving SIGINT the second time. Exit.")
        sys.exit(0)


def emit_labels(mqtt_client, mqtt_prefix, cfg_chips):
    for chip in cfg_chips:
        features = cfg_chips.get(chip, list())
        for feature in features['features'].values():
            topic = mqtt_prefix + feature['mqtt']
            label = feature.get('label')
            if label is not None:
                mqtt_client.publish(
                    "{}/Label".format(topic),
                    label
                )


def emit_chip_values(mqtt_client, mqtt_prefix, cfg_chips, sensor_chip):
    if str(sensor_chip) in cfg_chips:
        cfg_features = cfg_chips.get(str(sensor_chip), list())
        for sensor_feature in sensor_chip:
            cfg_feature = cfg_features['features'].get(sensor_feature.name)
            if cfg_feature is not None:
                print('  %s: %.2f' % (sensor_feature.label, sensor_feature.get_value()))
                topic = mqtt_prefix + cfg_feature['mqtt']
                print(topic)
                mqtt_client.publish(
                    "{}/Value".format(topic),
                    sensor_feature.get_value()
                )


def main():
    signal.signal(signal.SIGINT, sigint_handler)

    mqtt_config = mqtt.MqttConfig.from_env("MQTT_")
    mqtt_client = mqtt.create_client(mqtt_config)

    mqtt_prefix = mqtt_config.prefix

    cfg_chips = json.loads(util.load_env("SENSORS", "{}"))
    print("Running with sensors config:")
    print(json.dumps(cfg_chips, indent=4))

    emit_labels(mqtt_client, mqtt_prefix, cfg_chips)

    sensors.init()
    try:
        while running:
            for sensor_chip in sensors.iter_detected_chips():
                print('%s at %s' % (sensor_chip, sensor_chip.adapter_name))
                emit_chip_values(mqtt_client, mqtt_prefix, cfg_chips, sensor_chip)

            timer = 5
            while timer > 0 and running:
                time.sleep(1)
                timer = timer - 1

    finally:
        sensors.cleanup()

    if mqtt_client.is_connected():
        mqtt_client.loop_stop()


if __name__ == '__main__':
    main()
