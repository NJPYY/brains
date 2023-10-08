"""Support for Tuya sensors."""
from __future__ import annotations

from dataclasses import dataclass

from tuya_iot import TuyaDevice, TuyaDeviceManager
from tuya_iot.device import TuyaDeviceStatusRange

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from .brains_iot_sdk.const import (
    VALUE,
)
from .base import EnumTypeData, IntegerTypeData, BrainsEntity, BrainsDevice
from .device import HADeviceData
from .const import (
    DOMAIN,
    DISCOVER_BRAINS_DEVICE,
    DPType,
    UNITMAP,
)
from .device_structure import SENSORS


@dataclass
class TuyaSensorEntityDescription(SensorEntityDescription):
    """Describes Tuya sensor entity."""

    subkey: str | None = None

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Tuya sensor dynamically through Tuya discovery."""
    hass_data: HADeviceData = hass.data[DOMAIN][entry.entry_id]

    @callback
    def async_discover_device(device_ids: list[str]) -> None:
        """Discover and add a discovered Tuya sensor."""
        entities: list[TuyaSensorEntity] = []
        for device_id in device_ids:
            device: BrainsDevice = hass_data.device_manager.device_map[device_id]
            status_map: dict = {}
            for status in device.status:
                code: str = status["code"]
                status_map[code] = status
            if descriptions := SENSORS.get(device.device_type):
                for description in descriptions:
                    if description.key in status_map:
                        entities.append(
                            TuyaSensorEntity(
                                device, hass_data.device_manager, description, status_map
                            )
                        )

        async_add_entities(entities)

    async_discover_device([*hass_data.device_manager.device_map])

    entry.async_on_unload(
        async_dispatcher_connect(hass, DISCOVER_BRAINS_DEVICE, async_discover_device)
    )


class TuyaSensorEntity(BrainsEntity, SensorEntity):
    """Tuya Sensor Entity."""

    entity_description: TuyaSensorEntityDescription

    _status_range: TuyaDeviceStatusRange | None = None
    _type: DPType | None = None
    _type_data: IntegerTypeData | EnumTypeData | None = None

    def __init__(
        self,
        device: TuyaDevice,
        device_manager: TuyaDeviceManager,
        description: TuyaSensorEntityDescription,
        status_map: dict = None
    ) -> None:
        self.status_map = status_map
        """Init Tuya sensor."""
        super().__init__(device, device_manager)
        self.entity_description = description
        self._attr_unique_id = (
            f"{super().unique_id}{description.key}"
        )
        # 设置实体名称
        status = status_map[description.key]
        code: str = status["code"]
        arr: tuple = code.split("_")
        data_type = UNITMAP[arr[arr.__len__()-1]]
        self._attr_name = f"{status['name']}_{data_type}"

        if int_type := self.find_dpcode(description.key, dptype=DPType.INTEGER):
            self._type_data = int_type
            self._type = DPType.INTEGER
            if description.native_unit_of_measurement is None:
                self._attr_native_unit_of_measurement = int_type.unit
        elif enum_type := self.find_dpcode(
            description.key, dptype=DPType.ENUM, prefer_function=True
        ):
            self._type_data = enum_type
            self._type = DPType.ENUM
        else:
            self._type = self.get_dptype(description.key)


    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        # Only continue if data type is known
        if self._type not in (
            DPType.INTEGER,
            DPType.STRING,
            DPType.ENUM,
            DPType.JSON,
            DPType.RAW,
        ):
            return None
        # status_map: dict = {}
        # for status in self.device.status:
        #     status_map[status["code"]] = status
        # Raw value
        value = self.status_map.get(self.entity_description.key)[VALUE]
        if value is None:
            return None

        # Scale integer/float value
        if isinstance(self._type_data, IntegerTypeData):
            scaled_value = self._type_data.scale_value(value)
            return scaled_value

        # Unexpected enum value
        if (
            isinstance(self._type_data, EnumTypeData)
            and value not in self._type_data.range
        ):
            return None

        # # Get subkey value from Json string.
        # if self._type is DPType.JSON:
        #     if self.entity_description.subkey is None:
        #         return None
        #     values = ElectricityTypeData.from_json(value)
        #     return getattr(values, self.entity_description.subkey)

        # if self._type is DPType.RAW:
        #     if self.entity_description.subkey is None:
        #         return None
        #     values = ElectricityTypeData.from_raw(value)
        #     return getattr(values, self.entity_description.subkey)

        # Valid string or enum value
        return value
