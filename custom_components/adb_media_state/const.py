"""Constants for the ADB Media State integration."""
from __future__ import annotations

DOMAIN = "adb_media_state"
PLATFORMS = ["sensor"]

CONF_HOST = "host"
CONF_PORT = "port"
CONF_PACKAGE = "package"
CONF_NAME = "name"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_DETECT_PROGRAM = "detect_program"

DEFAULT_NAME = "Media State"
DEFAULT_PORT = 5555
DEFAULT_SCAN_INTERVAL = 15
DEFAULT_DETECT_PROGRAM = False

KEY_FILE = "adb_media_state_adbkey"

MODES = ("idle", "live", "program", "vod")

ATTR_APP = "app"
ATTR_TITLE = "title"
ATTR_SUBTITLE = "subtitle"
ATTR_ALBUM = "album"
ATTR_POSITION_MS = "position_ms"
ATTR_SPEED = "speed"
ATTR_ACTIONS = "actions"
ATTR_RAW_STATE = "raw_state"
ATTR_IS_LIVE = "is_live"
ATTR_IS_PROGRAM = "is_program"
ATTR_IS_VOD = "is_vod"
ATTR_TITLE_SOURCE = "title_source"


def entry_config(entry) -> dict:
    """Merge entry data and options; options always win."""
    return {**entry.data, **entry.options}
