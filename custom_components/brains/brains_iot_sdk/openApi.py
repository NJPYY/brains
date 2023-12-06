from __future__ import annotations

import logging

import requests
import json
from .device import BrainsDevice

from .const import (
    BASE_URL,
    TOKEN,
)

_LOGGER = logging.getLogger(__package__)


class BrainsApi:

    def __init__(self, secret_key: str, user_id: str):
        self.base_url = BASE_URL
        self.secret_key = secret_key
        self.user_id = user_id
        self.token = ""

    def get_token(self):
        data = {
            "userId": self.user_id,
            "secretKey": self.secret_key
        }
        headers = {
            'Content-Type': 'application/json; charset=UTF-8'
        }
        try:
            res = requests.post(url=f"{BASE_URL}/getToken", json=data, headers=headers)
            res_json = json.loads(res.text)
            _LOGGER.info(f"开始获取token =>{res_json}")
            self.token = res_json['data'][TOKEN]
            return json.loads(res.text), "ok"
        except:
            _LOGGER.warning(f"获取token失败 userId=>{self.user_id}")
            return None, "filed"

    def get_device_list(
        self,
        user_id: str = "",
        token: str = "",
        secret_key: str = ""
    ):
        self.user_id = user_id
        self.token = token
        self.secret_key = secret_key
        if not self.token:
            return
        """Get device list"""
        header = {
            "Authorization": "Bearer " + self.token
        }
        data = {
            "userId": self.user_id,
            "secretKey": self.secret_key
        }
        res = requests.get(f"{BASE_URL}/getDeviceList", params=data, headers=header)
        res_data = json.loads(res.text)

        device_list = []
        if res.status_code == 200 and res_data['success'] and res_data['data']:
            for device_json in res_data['data']:
                device = BrainsDevice.from_json(device_json)
                device_list.append(device)

        return device_list

    def get_device_map(
        self,
        user_id: str = "",
        token: str = "",
        secret_key: str = ""
    ):
        device_list = self.get_device_list(user_id=user_id, token=token, secret_key=secret_key)
        device_map: dict = {}
        for device in device_list:
            device_map[device.id] = device
        return device_map

    def get_device(self, device_id: str):
        """Add a device"""
        if not self.token:
            return
        header = {
            "Authorization": "Bearer " + self.token
        }
        data = {
            "userId": self.user_id,
            "deviceId": device_id,
            "secretKey": self.secret_key
        }
        res = requests.get(f"{BASE_URL}/getDeviceInfo", params=data, headers=header)
        device: BrainsDevice = None
        if res.status_code == 200:
            res_data = json.loads(res.text)
            if res_data["data"] and res_data["data"][0]:
                device = BrainsDevice.from_json(res_data["data"][0])
        return device

    def get_mq_config(self):
        if not self.token:
            return
        header = {
            "Authorization": "Bearer " + self.token
        }
        data = {
            "userId": self.user_id,
            "secretKey": self.secret_key
        }
        res = requests.get(f"{BASE_URL}/getMqConfig", params=data, headers= header)
        data = json.loads(res.text)
        _LOGGER.info(f"mq_config_data==>{data['data']}")
        return data['data']


