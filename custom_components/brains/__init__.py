"""The brains_iot_sdk integration."""
from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from .const import DOMAIN, CONF_TOKEN, CONF_USER_ID, CONF_SECRET_KEY, PLATFORMS

from .brains_iot_sdk import (
    BrainsApi,
    BrainsDevice,
    BrainsMq,
    DeviceManage
)

from .device import HADeviceListener, HADeviceData
# 设置日志
_LOGGER = logging.getLogger(__name__)




async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up brains from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # 获取设备列表
    user_id = entry.data[CONF_USER_ID]
    secret_key = entry.data[CONF_SECRET_KEY]
    token = entry.data[CONF_TOKEN]
    brains_api: BrainsApi = BrainsApi(user_id=user_id, secret_key=secret_key)
    brains_api.token = token
    device_map = await hass.async_add_executor_job(brains_api.get_device_map, user_id, token, secret_key)

    brains_mq = BrainsMq(brains_api)
    # brains_mq.add_message_listener(on_message)
    brains_mq.start()

    device_manager = DeviceManage(brains_mq)
    device_manager.device_map = device_map
    listener = HADeviceListener(hass, brains_api, entry, set(device_map.keys()))
    device_manager.add_listener(listener)

    # Get devices & clean up device entities
    # await hass.async_add_executor_job(home_manager.update_device_cache)
    # await cleanup_device_registry(hass, device_manager)

    # Migrate old unique_ids to the new format
    # async_migrate_entities_unique_ids(hass, entry, device_manager)

    # Register known device IDs
    device_registry = dr.async_get(hass)
    for device in device_manager.device_map.values():
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, device.id)},
            manufacturer="Brains",
            name=device.device_name,
            model=f"{device.device_type}",
        )
        # device_ids.add(device.id)

    ha_device_data = HADeviceData()
    ha_device_data.device_manager = device_manager
    hass.data[DOMAIN][entry.entry_id] = ha_device_data


    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def cleanup_device_registry(
    hass: HomeAssistant, device_manager: HADeviceManage
) -> None:
    """Remove deleted device registry entry if there are no remaining entities."""
    device_registry = dr.async_get(hass)
    for dev_id, device_entry in list(device_registry.devices.items()):
        for item in device_entry.identifiers:
            if item[0] == DOMAIN and item[1] not in device_manager.device_map:
                device_registry.async_remove_device(dev_id)
                break