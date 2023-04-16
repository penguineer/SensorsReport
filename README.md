# Sensors Report

> Watch pre-defined lmsensors values and post them to MQTT topics.

## Configuration

The following environment variables are expected:

* `MQTT_HOST` Name of the MQTT host
* `MQTT_TOPIC` Prefix for the MQTT topic
* `SENSORS` expects a JSON sensor configuration in the following form:
```json
{
  "<chip name>": {
    "features": {
      "<feature name>": {
        "label": "<feature label>",
        "mqtt": "<feature mqtt topic (added to prefix)>"
      }
    }
  }
}
```

In the above example, anything listed as `<...>` is meant to be replaced by a value described by the label with the brackets, e.g. `<chip name>` is written as `coretemp-isa-0000` without the brackets.

## Contributions

Contributions are welcome and should be made via PR.

Please not that for any more complicated use cases a fully fledged
monitoring system might be more appropriate.

## License

This project is published unter the MIT license.
