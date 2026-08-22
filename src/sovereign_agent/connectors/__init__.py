"""External system connectors. Integration is serialized contracts only."""

from .zero_employee import ConnectorError, TransportAck, ZeroEmployeeConnector

__all__ = ["ConnectorError", "TransportAck", "ZeroEmployeeConnector"]
