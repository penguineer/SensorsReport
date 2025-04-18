# Sensors Report

> Watch pre-defined [lm-sensors](https://github.com/lm-sensors/lm-sensors) values and post them to MQTT topics.

## Configuration

The following environment variables are expected:

* `LOG_LEVEL` Log level for the application. Possible values are `debug`, `info`, `warning`, `error`, `critical`, `notset`. Defaults to `info`.
* `MQTT_HOST` Name of the MQTT host
* `MQTT_TOPIC` Prefix for the MQTT topic
* `SENSORS` expects a JSON sensor configuration in the following form:
```json
{
  "sensors": [
    {
      "label": "<sensor feature label>",
      "topic": "<feature mqtt topic (added to prefix)>",
      "lm-sensors": {
        "chip": "<chip name>",
        "feature": "<feature name>"
      }
    },
    {
      "label": "<sensor feature label>",
      "topic": "<feature mqtt topic (added to prefix)>",
      "file": {
        "path": "<file path to read>"
      }
    }
  ]
}
```

In the above example, anything listed as `<...>` is meant to be replaced by a value described by the label with the brackets, e.g. `<chip name>` is written as `coretemp-isa-0000` without the brackets.
The top "sensors" object may seem redundant, but allows for future expansion of the configuration.

### Data Providers

The following data providers are available:
* **lm-sensors**: Reads the value from the lm-sensors chip and feature name.
  * `chip`: The name of the chip as shown by `sensors -l`
  * `feature`: The name of the feature as shown by `sensors -l` 
* **file**: Reads the value from a file.
  * `path`: The path to the file to read. The file must contain a single line with the value to be read. A final newline will be stripped.

## Running

With the configuration stored in a file `.env`, the tool can be started as follows:

```bash
docker run --rm \
  --env-file .env \
  mrtux/sensors-report
```

Alternatively there is a `docker-compose` set up to build and run from the repository.

For production use pre-built docker images are recommended.

## Contributions

Contributions are welcome and should be made via PR.

Please note that for any more complicated use cases a fully fledged
monitoring system might be more appropriate.

## License

[MIT](LICENSE) © 2021-2025 Stefan Haun and contributors
