"""Coordinator polling the device over ADB."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .adb_client import AdbError, AdbSession
from .const import (
    CONF_DETECT_PROGRAM,
    CONF_HOST,
    CONF_PACKAGE,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DOMAIN,
    KEY_FILE,
    entry_config,
)
from .parser import classify, parse_session

_LOGGER = logging.getLogger(__name__)

COMMAND = "dumpsys media_session"


class AdbMediaCoordinator(DataUpdateCoordinator[dict]):
    """Poll `dumpsys media_session` and classify what is playing."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        config = entry_config(entry)
        self._package: str | None = config.get(CONF_PACKAGE) or None
        self._detect_program: bool = bool(config.get(CONF_DETECT_PROGRAM, False))
        key_path = hass.config.path(".storage", KEY_FILE)
        self._adb = AdbSession(config[CONF_HOST], config[CONF_PORT], key_path)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {entry.title}",
            update_interval=timedelta(seconds=int(config[CONF_SCAN_INTERVAL])),
        )

    async def _async_update_data(self) -> dict:
        try:
            dump = await asyncio.wait_for(
                asyncio.to_thread(self._adb.shell, COMMAND), timeout=25
            )
        except (AdbError, asyncio.TimeoutError) as exc:
            raise UpdateFailed(f"ADB error: {exc}") from exc

        session = parse_session(dump, self._package)
        mode = classify(session, self._detect_program)
        return {"mode": mode, "session": session}

    async def async_shutdown(self) -> None:
        await asyncio.to_thread(self._adb.close)
        await super().async_shutdown()
