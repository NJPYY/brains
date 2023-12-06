from __future__ import annotations

from .device import BrainsDevice
from .device_listener import DeviceListener
import logging
from .openMq import BrainsMq

from .const import (
    ADD_DEVICE,
    DEL_DEVICE,
    CREATE_ALARM,
    CLEAR_ALARM,
    STATUS_CHANGE,
    VALUE_CHANGE,
    UPDATE_DEVICE,
    DEVICE_ID,
    DEVICE_STATE,
    MSG_TYPE,
    VALUES,
    ALARM_DATA,
    STATE,
    DEVICE_DATA,
    CODE,
    VALUE,
)
_LOGGER = logging.getLogger(__package__)


class DeviceManage:
    def __init__(self, mq: BrainsMq):
        self.device_map: dict[str, BrainsDevice] = {}
        self.device_listeners: set[DeviceListener] = set()
        self.mq = mq
        self.api = mq.api
        mq.add_message_listener(self.on_message)


    def on_message(self, msg):
        msg_type = msg[MSG_TYPE]
        if msg_type == UPDATE_DEVICE:
            self.update_device(msg)
        elif msg_type == ADD_DEVICE:
            self.add_device(msg)
        elif msg_type == VALUE_CHANGE:
            self.update_device_value(msg)
        elif msg_type == DEL_DEVICE:
            self.delete_device(msg)
        elif msg_type == STATUS_CHANGE:
            self.state_change(msg)
        elif msg_type == CREATE_ALARM:
            self.create_alarm(msg)
        elif msg_type == CLEAR_ALARM:
            self.clear_alarm(msg)
        
    def update_device_value(self, msg):
        _LOGGER.info(f"update device values, deviceId is {msg[DEVICE_ID]}, values is {msg[VALUES]}")
        values_map: dict = {}
        for value in msg[VALUES]["status"]:
            values_map[value[CODE]] = value[VALUE]
        device: BrainsDevice = self.device_map[msg[DEVICE_ID]]
        status = device.status
        new_status: list = []
        for item in status:
            if item[CODE] in values_map.keys():
                item[VALUE] = values_map[item[CODE]]
            new_status.append(item)
        device.status = new_status
        for listener in self.device_listeners:
            listener.update_device_value(msg)
        

    def delete_device(self, msg):
        _LOGGER.info(f"delete a device, deviceId is {msg[DEVICE_ID]}")
        device_id = msg[DEVICE_ID]
        if device_id in self.device_map.keys():
            del self.device_map[device_id]
        for listener in self.device_listeners:
            listener.delete_device(msg[DEVICE_ID])

    def state_change(self, msg):
        _LOGGER.info(f"update device`s state, new state is {msg[STATE]}")
        data = {
            DEVICE_ID: msg[DEVICE_ID],
            DEVICE_STATE: msg[STATE]
        }
        device: BrainsDevice = self.device_map[msg[DEVICE_ID]]
        device.online = msg[STATE]
        data = {
            DEVICE_ID: msg[DEVICE_ID],
            STATE: msg[STATE]
        }
        for listener in self.device_listeners:
            listener.state_change(data)

    def create_alarm(self, msg):
        _LOGGER.info(f"create a alarm")
        data = {
            DEVICE_ID: msg[DEVICE_ID],
            ALARM_DATA: msg[ALARM_DATA]
        }
        for listener in self.device_listeners:
            listener.create_alarm(data)
    
    def clear_alarm(self, msg):
        _LOGGER.info(f"clear a alarm")
        data = {
            DEVICE_ID: msg[DEVICE_ID],
            ALARM_DATA: msg[ALARM_DATA]
        }
        for listener in self.device_listeners:
            listener.clear_alarm(data)


    def add_device(self, msg):
        _LOGGER.info(f"add a new device, device_id data is {msg[DEVICE_ID]}")
        device_id = msg[DEVICE_ID]
        new_device = self.api.get_device(device_id)
        # device_data = msg[DEVICE_DATA]
        # new_device = BrainsDevice.from_json(device_data)
        self.device_map[new_device.id] = new_device
        for listener in self.device_listeners:
            listener.add_device(new_device)

    def update_device(self, msg):
        _LOGGER.info(f"update device info, new device info is {msg[DEVICE_ID]}")
        device_id = msg[DEVICE_ID]
        new_device = self.api.get_device(device_id)
        # device: BrainsDevice = BrainsDevice.from_json(msg[DEVICE_DATA])
        if not new_device:
            return
        self.device_map[new_device.id] = new_device
        for listener in self.device_listeners:
            listener.update_device(new_device)

    def add_listener(self, listener: DeviceListener):
        self.device_listeners.add(listener)
