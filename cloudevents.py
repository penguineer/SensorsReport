import uuid
from datetime import datetime


class CloudEventGenerator:
    """
    A generator for creating Cloud Events based on the [CloudEvents](https://cloudevents.io/) specification.
    """

    def __init__(self, source, event_type):
        """
        Initialize the CloudEventGenerator with fixed attributes.

        Args:
            source (str): The source of the event.
            event_type (str): The type of the event.
        """
        self.source = source
        self.type = event_type

    def generate(self, event_id=None, timestamp: datetime = None, subject=None, data=None):
        """
        Generate a Cloud Event with the provided or auto-generated attributes.

        Args:
            event_id (str, optional): The unique identifier for the event. Defaults to a UUID.
            timestamp (datetime, optional): The timestamp of the event. Defaults to the current time in ISO 8601 format.
            subject (str, optional): The subject of the event. Defaults to None.
            data (any, optional): The event payload. Defaults to None.

        Returns:
            dict: A dictionary representing the Cloud Event.
        """

        t = timestamp or datetime.now()

        return {
            "specversion": "1.0",
            "event_id": event_id or str(uuid.uuid4()),
            "source": self.source,
            "event_type": self.type,
            "time": t.astimezone().isoformat(),
            "subject": subject,
            "datacontenttype": "application/json",
            "data": data
        }
