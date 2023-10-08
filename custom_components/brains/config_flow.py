"""Config flow for brains_iot."""
from __future__ import annotations

from typing import Any
from homeassistant import config_entries
import voluptuous as vol
import logging

from .brains_iot_sdk import (
    BrainsApi,
)

from .const import (
    DOMAIN,
    CONF_USER_ID,
    CONF_SECRET_KEY,
    CONF_TOKEN,
)
_LOGGER = logging.getLogger(__package__)


class BrainsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    def __init__(self):
        pass

    @staticmethod
    def _try_login(user_input: dict[str, Any]) -> BrainsApi:
        """Try login."""
        secret_key = user_input[CONF_SECRET_KEY]
        user_id = user_input[CONF_USER_ID]

        brains_api = BrainsApi(secret_key=secret_key, user_id=user_id)
        brains_api.get_token()
        return brains_api


    async def async_step_user(self, user_input=None):
        errors = {}
        placeholders = {}

        if user_input is not None:
            _LOGGER.info(f"try to cinfig userInfo, userInput==>{user_input}")
            brains_api = await self.hass.async_add_executor_job(
                self._try_login, user_input
            )
            if brains_api and brains_api.token:
                _LOGGER.info(f"token==>{brains_api.token}")
            if brains_api.token:
                data = {
                    CONF_USER_ID: user_input[CONF_USER_ID],
                    CONF_SECRET_KEY: user_input[CONF_SECRET_KEY],
                    CONF_TOKEN: brains_api.token
                }
                return self.async_create_entry(
                    title=user_input[CONF_USER_ID],
                    data=data
                )
            errors["base"] = "login_error"

        if user_input is None:
            user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USER_ID,
                        default=user_input.get(CONF_USER_ID, ""),
                    ): str,
                    vol.Required(
                        CONF_SECRET_KEY, default=user_input.get(CONF_SECRET_KEY, "")
                    ): str,
                }
            ),
            errors=errors,
            description_placeholders=placeholders,
        )

