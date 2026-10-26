# Changelog

All notable changes to this project are documented here.
Versioning: CalVer (`YYYY.MM.PATCH`), git tag equals `manifest.json` version with a `v` prefix.

## v2026.10.0 — 2026-10-26

Initial public release.

- Sensor exposing the playback mode of one Android device + application pair:
  `idle`, `live`, `vod`, and (optionally) `program`.
- `live` detection from `dumpsys media_session` (`position < 0` or `speed == 0`) —
  independent of any metadata.
- Experimental `program` detection: VOD entries whose metadata fields 1 and 2 are
  identical (TV programmes that landed in a VOD catalogue). Off by default.
- Attributes: `app`, `title`, `subtitle`, `album`, `position_ms`, `speed`, `actions`,
  `raw_state`, `is_live`, `is_program`, `is_vod`.
- Config flow (UI) **and** YAML configuration (imported into a config entry).
- Options flow: poll interval, programme detection toggle.
- Multiple devices/apps: one config entry per `host:port:package`.
- Requires `adb-shell` (already shipped with Home Assistant for the `androidtv`
  integration; declared as a requirement with a lower bound, so nothing extra is
  installed when it is present).
