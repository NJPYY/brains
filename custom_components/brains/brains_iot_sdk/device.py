from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field
import json

from .const import (
    DEVICE_ID,
    DEVICE_TYPE,
    SITE_NAME,
    DEVICE_NAME,
    DEVICE_STATUS,
    ONLINE,
)

@dataclass
class BrainsDevice:

    def default_status(self):
        return {}
    """Brains Device.

    Attributes:
          id: Device id
          name: Device name
          online: Online status of the device

          status: Status set of the device
          function: Instruction set of the device
          status_range: Status value range set of the device
    """
    id: str | None = None
    device_name: str | None = None
    site_name: str | None = None
    device_type: str | None = None
    online: bool | None = None
    status: dict[str, Any] | None = field(default_factory=default_status)

    @classmethod
    def from_json(cls,  data: json) -> BrainsDevice | None:

        return cls(
            id=data[DEVICE_ID],
            device_name=data[DEVICE_NAME],
            site_name=data[SITE_NAME],
            device_type=data[DEVICE_TYPE],
            online=data.get(ONLINE, None),
            status=data.get(DEVICE_STATUS, None)
        )


