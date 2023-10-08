from __future__ import annotations

from enum import StrEnum
from homeassistant.const import Platform

PLATFORMS: list[Platform] = [
    Platform.NUMBER,
    Platform.SENSOR
    ]

"""Constants for the brains_iot_sdk integration."""

DOMAIN = "brains"

# 设备类型
DEVICE_TYPE = "device_type"


CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_TOKEN = "token"
CONF_USER_ID = "user_id"
CONF_SECRET_KEY = "secret_key"





class DPType(StrEnum):
    """Data point types."""

    BOOLEAN = "Boolean"
    ENUM = "Enum"
    INTEGER = "Integer"
    JSON = "Json"
    RAW = "Raw"
    STRING = "String"

# 通知标识
BRS_HA_SIGNAL_UPDATE_ENTITY = "brains_entry_update"
DISCOVER_BRAINS_DEVICE = "discover_brains_device"
UPDATE_BRAINS_DEVICE = "update_brains_device"
UNITMAP = {
    "I": "电流",
    "P": "功率",
    "U": "电压",
    "EP": "用电量"
}