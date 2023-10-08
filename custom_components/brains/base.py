"""Tuya Home Assistant Base Device Model."""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
from .brains_iot_sdk import BrainsDevice, DeviceManage

from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, Entity

from .const import DOMAIN, BRS_HA_SIGNAL_UPDATE_ENTITY, DPType


@dataclass
class IntegerTypeData:
    """Integer Type Data."""

    min: int
    max: int
    # scale: float
    step: float
    unit: str | None = None
    type: str | None = None

    @property
    def max_scaled(self) -> float:
        """Return the max scaled."""
        return self.scale_value(self.max)

    @property
    def min_scaled(self) -> float:
        """Return the min scaled."""
        return self.scale_value(self.min)

    @property
    def step_scaled(self) -> float:
        """Return the step scaled."""
        return self.step

    def scale_value(self, value: float | int) -> float:
        """Scale a value."""
        return value

    def scale_value_back(self, value: float | int) -> int:
        """Return raw value for scaled."""
        return int(value)

    def remap_value_to(
        self,
        value: float,
        to_min: float | int = 0,
        to_max: float | int = 255,
        reverse: bool = False,
    ) -> float:
        """Remap a value from this range to a new range."""
        return remap_value(value, self.min, self.max, to_min, to_max, reverse)

    def remap_value_from(
        self,
        value: float,
        from_min: float | int = 0,
        from_max: float | int = 255,
        reverse: bool = False,
    ) -> float:
        """Remap a value from its current range to this range."""
        return remap_value(value, from_min, from_max, self.min, self.max, reverse)

    @classmethod
    def from_json(cls,  data: json) -> IntegerTypeData | None:
        """Load JSON string and return a IntegerTypeData object."""
        # if not (parsed := json.loads(data)):
        #     return None

        return cls(
            min=int(data["min"]),
            max=int(data["max"]),
            # scale=float(data["scale"]),
            step=max(float(data["step"]), 1),
            unit=data.get("unit"),
            type=data.get("type"),
        )


@dataclass
class EnumTypeData:
    """Enum Type Data."""

    range: list[str]

    @classmethod
    def from_json(cls, data: json) -> EnumTypeData | None:
        """Load JSON string and return a EnumTypeData object."""
        return cls(**data)


# @dataclass
# class ElectricityTypeData:
#     """Electricity Type Data."""

#     electriccurrent: str | None = None
#     power: str | None = None
#     voltage: str | None = None

#     @classmethod
#     def from_json(cls, data: str) -> Self:
#         """Load JSON string and return a ElectricityTypeData object."""
#         return cls(**json.loads(data.lower()))

#     @classmethod
#     def from_raw(cls, data: str) -> Self:
#         """Decode base64 string and return a ElectricityTypeData object."""
#         raw = base64.b64decode(data)
#         voltage = struct.unpack(">H", raw[0:2])[0] / 10.0
#         electriccurrent = struct.unpack(">L", b"\x00" + raw[2:5])[0] / 1000.0
#         power = struct.unpack(">L", b"\x00" + raw[5:8])[0] / 1000.0
#         return cls(
#             electriccurrent=str(electriccurrent), power=str(power), voltage=str(voltage)
#         )


class BrainsEntity(Entity):
    """Tuya base device."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, device: BrainsDevice, device_manager: DeviceManage) -> None:
        """Init BrainsHaEntity."""
        self._attr_unique_id = f"brains.{device.id}"
        self.device = device
        self.device_manager = device_manager

    @property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.device.id)},
            manufacturer="Brains",
            name=self.device.device_name,
        )

    @property
    def available(self) -> bool:
        """Return if the device is available.
            判断当前device是否可用
        """
        return self.device.online

    # @overload
    # def find_dpcode(
    #     self,
    #     dpcodes: str | DPCode | tuple[DPCode, ...] | None,
    #     *,
    #     prefer_function: bool = False,
    #     dptype: Literal[DPType.ENUM],
    # ) -> EnumTypeData | None:
    #     ...

    # @overload
    # def find_dpcode(
    #     self,
    #     dpcodes: str | DPCode | tuple[DPCode, ...] | None,
    #     *,
    #     prefer_function: bool = False,
    #     dptype: Literal[DPType.INTEGER],
    # ) -> IntegerTypeData | None:
    #     ...

    # @overload
    # def find_dpcode(
    #     self,
    #     dpcodes: str | DPCode | tuple[DPCode, ...] | None,
    #     *,
    #     prefer_function: bool = False,
    # ) -> DPCode | None:
    #     ...

    def find_dpcode(
        self,
        dpcode: str | None,
        *,
        dptype: DPType | None = None,
    ) -> EnumTypeData | IntegerTypeData | None:
        """Find a matching DP code available on for this device."""
        if dpcode is None:
            return None

        key = "status"
        # status: tuple[dict[str: Any]] = json.loads(self.device.status)
        status = self.device.status

        for statu in status:
            if dpcode != statu["code"]:
                continue
            if ( dptype == DPType.ENUM and statu["type"] == DPType.ENUM ):
                if not ( enum_type := EnumTypeData.from_json(statu["value_range"])):
                    return None
                return enum_type

            if (dptype == DPType.INTEGER and statu["type"] == DPType.INTEGER):
                if not (integer_type := IntegerTypeData.from_json(statu["value_range"])):
                    return None
                return integer_type

            if dptype not in (DPType.ENUM, DPType.INTEGER):
                return dpcode

        return None

    def get_dptype(
        self, dpcode: str
    ) -> DPType | None:
        """Find a matching DPCode data type available on for this device."""
        if dpcode is None:
            return None
        # status: tuple[dict[str: Any]] = json.loads(self.device.status)
        for code_status in self.device.status:
            if code_status["code"] != dpcode:
                continue
            if code_status["type"] in (DPType):
                return DPType(code_status["type"])

        return None

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{BRS_HA_SIGNAL_UPDATE_ENTITY}_{self.device.id}",
                self.async_write_ha_state,
            )
        )

    # def _send_command(self, commands: list[dict[str, Any]]) -> None:
    #     """Send command to the device."""
    #     LOGGER.debug("Sending commands for device %s: %s", self.device.id, commands)
    #     self.device_manager.send_commands(self.device.id, commands)


def remap_value(
    value: float | int,
    from_min: float | int = 0,
    from_max: float | int = 255,
    to_min: float | int = 0,
    to_max: float | int = 255,
    reverse: bool = False,
) -> float:
    """Remap a value from its current range, to a new range."""
    if reverse:
        value = from_max - value + from_min
    return ((value - from_min) / (from_max - from_min)) * (to_max - to_min) + to_min