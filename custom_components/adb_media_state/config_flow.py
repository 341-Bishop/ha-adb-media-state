"""Config flow and options flow for ADB Media State."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .adb_client import AdbError, AdbSession
from .const import (
    CONF_DETECT_PROGRAM,
    CONF_HOST,
    CONF_NAME,
    CONF_PACKAGE,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_DETECT_PROGRAM,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    KEY_FILE,
)

_LOGGER = logging.getLogger(__name__)

DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_PACKAGE, default=""): str,
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            int, vol.Range(min=5, max=3600)
        ),
        vol.Required(
            CONF_DETECT_PROGRAM, default=DEFAULT_DETECT_PROGRAM
        ): bool,
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            int, vol.Range(min=5, max=3600)
        ),
        vol.Required(
            CONF_DETECT_PROGRAM, default=DEFAULT_DETECT_PROGRAM
        ): bool,
    }
)


def _unique_id(data: dict[str, Any]) -> str:
    package = (data.get(CONF_PACKAGE) or "").strip() or "*"
    return f"{data[CONF_HOST]}:{data[CONF_PORT]}:{package}"


async def _validate(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Connect to the device and make sure a media session dump is readable."""
    key_path = hass.config.path(".storage", KEY_FILE)
    session = AdbSession(data[CONF_HOST], data[CONF_PORT], key_path)

    def _probe() -> None:
        dump = session.shell("dumpsys media_session")
        if "MEDIA SESSION SERVICE" not in dump and "Sessions Stack" not in dump:
            raise AdbError("unexpected response to 'dumpsys media_session'")

    try:
        await asyncio.wait_for(asyncio.to_thread(_probe), timeout=30)
    except (AdbError, asyncio.TimeoutError) as exc:
        raise ValueError(str(exc)) from exc
    finally:
        await asyncio.to_thread(session.close)


class AdbMediaStateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the device/app setup."""

    VERSION = 1

    async def _async_create(self, data: dict[str, Any]) -> FlowResult:
        await self.async_set_unique_id(_unique_id(data))
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=data[CONF_NAME], data=data)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await _validate(self.hass, user_input)
            except ValueError:
                errors["base"] = "cannot_connect"
            else:
                return await self._async_create(user_input)

        return self.async_show_form(
            step_id="user", data_schema=DEVICE_SCHEMA, errors=errors
        )

    async def async_step_import(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Import an entry defined in YAML."""
        if user_input is None:
            return self.async_abort(reason="import_failed")
        return await self._async_create(dict(user_input))

    @staticmethod
    @callback
    def async_get_options_flow(entry: config_entries.ConfigEntry):
        return AdbMediaStateOptionsFlow(entry)


class AdbMediaStateOptionsFlow(config_entries.OptionsFlow):
    """Adjust the polling interval and the experimental programme detection."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        merged = {**self._entry.data, **self._entry.options}
        schema = self.add_suggested_values_to_schema(
            OPTIONS_SCHEMA,
            {
                CONF_SCAN_INTERVAL: merged.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                ),
                CONF_DETECT_PROGRAM: merged.get(
                    CONF_DETECT_PROGRAM, DEFAULT_DETECT_PROGRAM
                ),
            },
        )
        return self.async_show_form(step_id="init", data_schema=schema)
