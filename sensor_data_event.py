from cloudevents import CloudEventGenerator


class SensorDataEvent:
    """
    Represents a measurement from one sensor.

    Attributes:
        sensor_config (dict): The configuration of the sensor that created the event, as provided in the sensor's configuration.
        value (float): The measured value from the sensor.
    """

    def __init__(self, sensor_config, value):
        self.sensor_config = sensor_config
        self.value = value

    def __repr__(self):
        return f"SensorDataEvent(sensor_config={self.sensor_config}, value={self.value})"

    def as_cloud_event_data(self, generator):
        """
        Convert the SensorDataEvent to a CloudEvent data format.

        Returns:
            dict: A dictionary representing the sensor's CloudEvent data portion.
        """
        return generator.generate(
            subject=self.sensor_config['topic'],
            data={
                "sensor_config": self.sensor_config,
                "value": self.value
            })

    def topic(self) -> str:
        """
        Get the topic for the sensor event.

        Returns:
            str: The topic for the sensor event.
        """
        return self.sensor_config['topic']
