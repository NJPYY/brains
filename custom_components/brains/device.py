from __future__ import annotations

from .brains_iot_sdk import DeviceListener, DeviceManage, BrainsMq, BrainsApi, BrainsDevice
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from .const import (
    DOMAIN,
    DISCOVER_BRAINS_DEVICE,
    BRS_HA_SIGNAL_UPDATE_ENTITY,
)

_LOGGER = logging.getLogger(__package__)

class HADeviceListener(DeviceListener):

    def __init__(self, hass: HomeAssistant, api: BrainsApi, entry: ConfigEntry, device_ids: set[str]) -> None:
        super().__init__()
        self._hass = hass
        self.api = api
        self.entry = entry
        self.device_ids = device_ids

    def update_device(self, device: BrainsDevice):
        _LOGGER.info(f"homeassistant update device info, new device is {device}")
        """Update device info.

        Args:
            device_id: str
        """
        dispatcher_send(self._hass, DISCOVER_BRAINS_DEVICE, [device.id])
    def add_device(self, new_device: BrainsDevice):
        _LOGGER.info(f"Add a device from brains cloud, new_device is {new_device}")
        if new_device.id in self.device_ids:
            return
        self._hass.add_job(self.async_remove_device, new_device.id)
        # device_registry = dr.async_get(self._hass)
        # device_registry.async_get_or_create(
        #     config_entry_id=self.entry.entry_id,
        #     identifiers={(DOMAIN, new_device.id)},
        #     manufacturer="Brains",
        #     name=new_device.device_name,
        #     model=f"{new_device.device_type}",
        # )
        dispatcher_send(self._hass, DISCOVER_BRAINS_DEVICE, [new_device.id])

    def delete_device(self, device_id: str):
        _LOGGER.info(f"Remove a device from homeassistant, device_id is {device_id}")
        self._hass.add_job(self.async_remove_device, device_id)
        

    def update_device_value(self, data):
        _LOGGER.info(
            f"The value of the device has changed, update homeassistant device data, device_id is {data['deviceId']}, data is {data['values']}")
        """update device value.
            {
                deviceId: xxx,
                data: [
                    {
                        code: xxxx,
                        value: xxxx
                    }
                ]
            }
        """
        dispatcher_send(self._hass, f"{BRS_HA_SIGNAL_UPDATE_ENTITY}_{data['deviceId']}")

    def state_change(self, data):
        _LOGGER.info(f"The state of device has changed, deviceId is {data['deviceId']}")
        """update device state.
            {
                deviceId: xxx,
                state: xxx
            }
        """
        dispatcher_send(self._hass, f"{BRS_HA_SIGNAL_UPDATE_ENTITY}_{data['deviceId']}")

    def create_alarm(self, data):
        _LOGGER.info(f"create a alarm, device_id is {data['deviceId']}")
        """create a device alarm.
            {
                "deviceId": xxx,
                "data":{
                    "alarm_type": xxxx,
                    "value": 230
                }
            }
        """
        pass

    def clear_alarm(self, data):
        _LOGGER.info(f"clear a alarm, device_id is {data['deviceId']}")
        """clear a device alarm.
            {
                "deviceId": xxx,
                "data":{
                    "alarm_type": xxxx,
                    "value": 220
                }
            }
        """
        pass


    @callback
    def async_remove_device(self, device_id: str) -> None:
        """Remove device from Home Assistant."""
        _LOGGER.debug("Remove device: %s", device_id)
        device_registry = dr.async_get(self._hass)
        device_entry = device_registry.async_get_device(
            identifiers={(DOMAIN, device_id)}
        )
        if device_entry is not None:
            device_registry.async_remove_device(device_entry.id)
            self.device_ids.discard(device_id)


class HADeviceData:
    device_manager: DeviceManage
    device_listener: DeviceListener



