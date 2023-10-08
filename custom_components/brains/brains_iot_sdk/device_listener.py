from __future__ import annotations

import logging
from abc import ABCMeta, abstractclassmethod

LOGGER = logging.getLogger(__package__)


class DeviceListener(metaclass=ABCMeta):

    @abstractclassmethod
    def update_device(self, device):
        """Update device info.

        Args:
            device_id: str
        """
        pass

    @abstractclassmethod
    def add_device(self,  device_id: str):
        """Device Added.

        Args:
            device_id: str
        """
        pass

    @abstractclassmethod
    def delete_device(self, device_id: str):
        """delete a Device.

        Args:
            device_id: str
        """
        pass

    @abstractclassmethod
    def update_device_value(self, data):
        """update device value.
            {
                device_id: xxx,
                data: [
                    {
                        code: xxxx,
                        value: xxxx
                    }
                ]
            }
        """
        pass

    @abstractclassmethod
    def state_change(self, data):
        """update device state.
            {
                device_id: xxx,
                state: xxx
            }
        """
        pass

    @abstractclassmethod
    def create_alarm(self, data):
        """create a device alarm.
            {
                "device_id": xxx,
                "data":{
                    "alarm_type": xxxx,
                    "value": 230
                }
            }
        """
        pass

    @abstractclassmethod
    def clear_alarm(self, data):
        """clear a device alarm.
            {
                "device_id": xxx,
                "data":{
                    "alarm_type": xxxx,
                    "value": 220
                }
            }
        """
        pass