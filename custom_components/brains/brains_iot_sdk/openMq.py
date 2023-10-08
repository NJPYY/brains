from __future__ import annotations

from urllib.parse import urlsplit
from typing import Optional

import paho.mqtt.client as mqtt
import logging
import base64
import json
import threading
import time
from typing import Any, Callable

from .openApi import BrainsApi
from .const import (
    CONNECT_FAILED_NOT_AUTHORISED,
    MQ_TOPIC,
    MSG_TYPE,
)

LOGGER = logging.getLogger(__package__)

class BrainsMQConfig:
    """Tuya mqtt config."""

    def __init__(self, config: dict) -> None:
        """Init TuyaMQConfig."""
        self.url = config.get("url", "")
        self.client_id = config.get("clientId", "")
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        self.topics = config.get("topic", [])
        self.expire_time = config.get("expire_time", 0)


class BrainsMq(threading.Thread):
    def __init__(self, api: BrainsApi) -> None:
        """Init TuyaOpenMQ."""
        threading.Thread.__init__(self)
        self.api: BrainsApi = api
        self._stop_event = threading.Event()
        self.client = None
        self.mq_config = None
        self.message_listeners = set()

    def _get_mqtt_config(self) -> Optional[BrainsMQConfig]:
        mq_config_data = self.api.get_mq_config()
        mq_config = BrainsMQConfig(mq_config_data)
        if not mq_config:
            return None
        return mq_config

    def _decode_mq_message(self, b64msg: str, password: str, t: str) -> dict[str, Any]:
        #TODO 解密
        return b64msg

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            LOGGER.error(f"Unexpected disconnection.{rc}")
        else:
            LOGGER.debug("disconnect")

    def _on_connect(self, mqttc: mqtt.Client, user_data: Any, flags, rc):
        LOGGER.debug(f"connect flags->{flags}, rc->{rc}")
        if rc == 0:
            for value in self.mq_config.topics:
                mqttc.subscribe(value)
        elif rc == CONNECT_FAILED_NOT_AUTHORISED:
            self.__run_mqtt()

    def _on_message(self, mqttc: mqtt.Client, user_data: Any, msg: mqtt.MQTTMessage):
        LOGGER.debug(f"payload-> {msg.payload}")

        msg_dict = json.loads(msg.payload.decode("utf8"))

        # t = msg_dict.get("data", "")

        # mq_config = user_data["mqConfig"]
        # decrypted_data = self._decode_mq_message(
        #     msg_dict["data"], mq_config.password, t
        # )
        # if decrypted_data is None:
        #     return

        # msg_dict["data"] = decrypted_data
        # LOGGER.debug(f"on_message: {msg_dict}")

        if not msg_dict:
            return
        for listener in self.message_listeners:
            listener(msg_dict)

    def _on_subscribe(self, mqttc: mqtt.Client, user_data: Any, mid, granted_qos):
        LOGGER.debug(f"_on_subscribe: {mid}")

    def _on_log(self, mqttc: mqtt.Client, user_data: Any, level, string):
        LOGGER.debug(f"_on_log: {string}")

    def run(self):
        """Method representing the thread's activity which should not be used directly."""
        while not self._stop_event.is_set():
            self.__run_mqtt()

            # reconnect every 2 hours required.
            time.sleep(self.mq_config.expire_time - 60)

    def __run_mqtt(self):
        mq_config = self._get_mqtt_config()
        if mq_config is None:
            LOGGER.error("error while get mqtt config")
            return

        self.mq_config = mq_config

        LOGGER.debug(f"connecting {mq_config.url}")
        mqttc = self._start(mq_config)

        if self.client:
            self.client.disconnect()
        self.client = mqttc

    def _start(self, mq_config: BrainsMQConfig) -> mqtt.Client:
        mqttc = mqtt.Client(mq_config.client_id)
        mqttc.username_pw_set(mq_config.username, mq_config.password)
        mqttc.user_data_set({"mqConfig": mq_config})
        mqttc.on_connect = self._on_connect
        mqttc.on_message = self._on_message
        mqttc.on_subscribe = self._on_subscribe
        mqttc.on_log = self._on_log
        mqttc.on_disconnect = self._on_disconnect

        url = urlsplit(mq_config.url)
        if url.scheme == "ssl":
            mqttc.tls_set()

        mqttc.connect(url.hostname, url.port)

        mqttc.loop_start()
        return mqttc

    def start(self):
        """Start mqtt.

        Start mqtt thread
        """
        LOGGER.debug("start")
        super().start()

    def stop(self):
        """Stop mqtt.

        Stop mqtt thread
        """
        LOGGER.debug("stop")
        self.message_listeners = set()
        self.client.disconnect()
        self.client = None
        self._stop_event.set()

    def add_message_listener(self, listener: Callable[[str], None]):
        """Add mqtt message listener."""
        self.message_listeners.add(listener)

    def remove_message_listener(self, listener: Callable[[str], None]):
        """Remvoe mqtt message listener."""
        self.message_listeners.discard(listener)
