from __future__ import annotations
"""数字类型的实体"""

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .brains_iot_sdk import BrainsDevice, DeviceManage
from .brains_iot_sdk.const import VALUE
from .device import HADeviceData
from .const import DOMAIN, DPType, DISCOVER_BRAINS_DEVICE, UNITMAP
from .base import IntegerTypeData, BrainsEntity

from .device_structure import NUMBERS


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Tuya number dynamically through Tuya discovery."""
    hass_data: HADeviceData = hass.data[DOMAIN][entry.entry_id]

    @callback
    def async_discover_device(device_ids: list[str]) -> None:
        """Discover and add a discovered Tuya number."""
        entities: list[BrainsNumberEntity] = []
        for device_id in device_ids:
            device = hass_data.device_manager.device_map[device_id]
            if descriptions := NUMBERS.get(device.device_type):
                for description in descriptions:
                    status_map: dict = {}
                    for status in device.status:
                        code: str = status["code"]
                        status_map[code] = status
                    if description.key in status_map:
                        entities.append(
                            BrainsNumberEntity(
                                device, hass_data.device_manager, description, status_map
                            )
                        )

        async_add_entities(entities)

    async_discover_device([*hass_data.device_manager.device_map])
    entry.async_on_unload(
        async_dispatcher_connect(hass, DISCOVER_BRAINS_DEVICE, async_discover_device)
    )


class BrainsNumberEntity(BrainsEntity, NumberEntity):
    """Brains Number Entity."""

    _number: IntegerTypeData | None = None

    def __init__(
        self,
        device: BrainsDevice,
        device_manager: DeviceManage,
        description: NumberEntityDescription,
        status_map: dict
    ) -> None:
        """Init Brains sensor."""
        super().__init__(device, device_manager)
        self.entity_description = description
        self._attr_unique_id = f"{super().unique_id}{description.key}"
        self.status_map = status_map
        # 设置实体名称
        status = status_map[description.key]
        code: str = status["code"]
        arr: tuple = code.split("_")
        data_type = UNITMAP[arr[arr.__len__()-1]]
        self._attr_name = f"{status['name']}_{data_type}"
        
        if int_type := self.find_dpcode(
            description.key, dptype=DPType.INTEGER
        ):
            self._number = int_type
            self._attr_native_max_value = self._number.max_scaled
            self._attr_native_min_value = self._number.min_scaled
            self._attr_native_step = self._number.step_scaled

        # Logic to ensure the set device class and API received Unit Of Measurement
        # match Home Assistants requirements.
        # if (
        #     self.device_class is not None
        #     and not self.device_class.startswith(DOMAIN)
        #     and description.native_unit_of_measurement is None
        # ):
        #     # We cannot have a device class, if the UOM isn't set or the
        #     # device class cannot be found in the validation mapping.
        #     if (
        #         self.native_unit_of_measurement is None
        #         or self.device_class not in DEVICE_CLASS_UNITS
        #     ):
        #         self._attr_device_class = None
        #         return

        #     uoms = DEVICE_CLASS_UNITS[self.device_class]
        #     self._uom = uoms.get(self.native_unit_of_measurement) or uoms.get(
        #         self.native_unit_of_measurement.lower()
        #     )

        #     # Unknown unit of measurement, device class should not be used.
        #     if self._uom is None:
        #         self._attr_device_class = None
        #         return

        #     # If we still have a device class, we should not use an icon
        #     if self.device_class:
        #         self._attr_icon = None

        #     # Found unit of measurement, use the standardized Unit
        #     # Use the target conversion unit (if set)
        #     self._attr_native_unit_of_measurement = (
        #         self._uom.conversion_unit or self._uom.unit
        #     )

    @property
    def native_value(self) -> float | None:
        """Return the entity value to represent the entity state."""
        # Unknown or unsupported data type
        if self._number is None:
            return None
        # status_map: dict = {}
        # for status in self.device.status:
        #     status_map[status["code"]] = status

        # Raw value
        if (value := self.status_map.get(self.entity_description.key)[VALUE]) is None:
            return None

        return self._number.scale_value(value)

    def set_native_value(self, value: float) -> None:
        """Set new value."""
        if self._number is None:
            raise RuntimeError("Cannot set value, device doesn't provide type data")

        # self._send_command(
        #     [
        #         {
        #             "code": self.entity_description.key,
        #             "value": self._number.scale_value_back(value),
        #         }
        #     ]
        # )