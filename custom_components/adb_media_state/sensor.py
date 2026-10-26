"""Sensor exposing the classified playback mode."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ACTIONS,
    ATTR_ALBUM,
    ATTR_APP,
    ATTR_IS_LIVE,
    ATTR_IS_PROGRAM,
    ATTR_IS_VOD,
    ATTR_POSITION_MS,
    ATTR_RAW_STATE,
    ATTR_SPEED,
    ATTR_SUBTITLE,
    ATTR_TITLE,
    ATTR_TITLE_SOURCE,
    CONF_NAME,
    DOMAIN,
)
from .coordinator import AdbMediaCoordinator

ICONS = {
    "idle": "mdi:television-off",
    "live": "mdi:broadcast",
    "program": "mdi:television-classic",
    "vod": "mdi:movie-open",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Register the sensor for this entry."""
    coordinator: AdbMediaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AdbMediaStateSensor(coordinator, entry)])


class AdbMediaStateSensor(CoordinatorEntity[AdbMediaCoordinator], SensorEntity):
    """Playback mode of one device/app pair."""

    _attr_has_entity_name = False

    def __init__(self, coordinator: AdbMediaCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._name: str = entry.data[CONF_NAME]
        self._attr_name = self._name
        self._attr_unique_id = f"{entry.unique_id}_state"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(entry.unique_id))},
            name=self._name,
            manufacturer="ADB Media State",
            model="MediaSession poller",
        )

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("mode")

    @property
    def icon(self) -> str:
        return ICONS.get(self.native_value or "idle", "mdi:television-classic")

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or {}
        session = data.get("session")
        mode = data.get("mode")
        if session is None:
            return {
                ATTR_APP: "",
                ATTR_TITLE: "",
                ATTR_SUBTITLE: "",
                ATTR_ALBUM: "",
                ATTR_RAW_STATE: "idle",
                ATTR_IS_LIVE: False,
                ATTR_IS_PROGRAM: False,
                ATTR_IS_VOD: False,
            }
        return {
            ATTR_APP: session.package,
            ATTR_TITLE: session.title,
            ATTR_SUBTITLE: session.subtitle,
            ATTR_ALBUM: session.album,
            ATTR_POSITION_MS: session.position,
            ATTR_SPEED: session.speed,
            ATTR_ACTIONS: session.actions,
            ATTR_RAW_STATE: session.state,
            ATTR_IS_LIVE: mode == "live",
            ATTR_IS_PROGRAM: mode == "program",
            ATTR_IS_VOD: mode == "vod",
            ATTR_TITLE_SOURCE: "media_session.description",
        }
