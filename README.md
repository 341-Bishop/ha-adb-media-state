# ADB Media State

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Home Assistant custom integration that reports **what an Android device is playing**, read
straight from the system media session over ADB. Works with Android TV / Google TV boxes,
phones, tablets — anything with `dumpsys media_session` and ADB debugging enabled.

Unlike cast-based integrations it sees **native app playback** (Netflix, HBO Max, Prime Video,
Disney+, YouTube, Jellyfin, VLC…), and unlike screenshot-based solutions it is not blocked by DRM.

> **PL:** Integracja odczytuje przez ADB stan sesji multimedialnej i wystawia sensor z trybem
> odtwarzania (`idle` / `live` / `vod`, opcjonalnie `program`). Działa z natywnymi aplikacjami,
> których nie widać przez Cast, i nie przeszkadza jej DRM.

---

## What you get

One sensor per configured *device + application* pair:

| state | meaning | how it is detected |
|---|---|---|
| `idle` | nothing playing (app menu, launcher, device idle) | no session, or `STOPPED`/`ERROR` |
| `live` | linear stream / TV channel | `position < 0` **or** `speed == 0` — hard signal |
| `vod` | film / series / any on-demand playback | everything else that is playing |
| `program` | on-demand **TV programme** (e.g. a show that also airs live) | metadata field 1 == field 2 — **experimental**, off by default |

Attributes: `app`, `title`, `subtitle`, `album`, `position_ms`, `speed`, `actions`, `raw_state`,
`is_live`, `is_program`, `is_vod`, `title_source`.

Notes on metadata, learned from real devices:

- `title` is the film title or the **episode** title,
- `subtitle` is often the **series** title,
- some apps (Netflix, Disney+, Prime Video) publish neither — you still get the app and the state,
- during a live stream the app may publish no position/duration at all (that is why `live`
  is detected from `position`/`speed`, not from a missing duration).

## Requirements

- Home Assistant 2024.6 or newer (container, core or supervised).
- ADB debugging enabled on the target device, port 5555 reachable from Home Assistant.
- `adb-shell` — a pure-Python library that Home Assistant already ships (it powers the built-in
  `androidtv` integration). Declared as a requirement with a lower bound, so when it is present
  nothing extra is installed. **No `adb` binary and no sidecar container are needed.**

## Installation

### HACS (custom repository)

1. HACS → three-dot menu → **Custom repositories** → add
   `https://github.com/341-Bishop/ha-adb-media-state`, category **Integration**.
2. Install **ADB Media State**, restart Home Assistant.
3. Settings → Devices & services → **Add integration** → *ADB Media State*.

Updates: HACS compares the installed version with the latest release tag — no manual file copying.

### Manual

Copy `custom_components/adb_media_state/` into your `/config/custom_components/` directory and
restart Home Assistant.

## Configuration

### UI (config flow)

| field | meaning |
|---|---|
| Entity name | also becomes the entity id (`1_lvn_hbo` → `sensor.1_lvn_hbo`) |
| Device IP / ADB port | e.g. `192.168.1.31`, `5555` |
| Application package | `com.wbd.stream`, `com.netflix.ninja`, … or empty for *any* app |
| Poll interval | seconds, 5–3600 (default 15) |
| Detect TV programmes | experimental heuristic, default off |

On the first connection the device shows an authorization prompt — tick *always allow*.
The integration generates its own RSA key in `/config/.storage/adb_media_state_adbkey`.

### YAML

```yaml
adb_media_state:
  - name: 1_lvn_hbo
    host: 192.168.1.31
    port: 5555
    package: com.wbd.stream
    scan_interval: 10
    detect_program: true

  - name: 1_lvn_netflix
    host: 192.168.1.31
    package: com.netflix.ninja
```

YAML entries are imported into config entries on startup (an import flow), so they behave exactly
like UI entries. Changing YAML requires a Home Assistant restart. Options that are not set in YAML
can still be adjusted later in the UI.

## Multiple devices

One entry per `host:port:package`. A TV running several apps gives several sensors
(`sensor.1_lvn_hbo`, `sensor.1_lvn_netflix`, …) — the entity name tells you which app is covered.

## Renaming

The entity id comes from the name you provide. You can rename it at any time:
**Settings → Devices & services → Entities → (entity) → settings icon → Entity ID**.
The unique id stays stable, so nothing is duplicated or orphaned.

## Automation example

```yaml
automation:
  - alias: Cinema lights when a film starts
    triggers:
      - trigger: state
        entity_id: sensor.1_lvn_hbo
        to: "vod"
    conditions:
      - condition: state
        entity_id: sensor.1_lvn_hbo
        attribute: is_live
        state: false
    actions:
      - action: scene.turn_on
        target:
          entity_id: scene.cinema
```

Because `live` and `program` are separate states, you can simply ignore channels and TV
programmes — they never become `vod`.

## Troubleshooting

| Symptom | Check |
|---|---|
| `cannot_connect` during setup | ADB debugging on? port 5555 open? authorization prompt accepted? another ADB client holding the connection? |
| entity `unavailable` | nothing was read — network/ADB problem, or the device is off (this is intentional, unlike MQTT-retained sensors) |
| always `idle` | wrong package name, or the app publishes no media session (some apps use their own player) |
| `program` never appears | the heuristic is disabled, or the app does not fill metadata fields 1 and 2 |
| Netflix shows `playing` while browsing | Netflix video previews create a real session — disable previews in the app |

Logs: **Settings → System → Logs**, filter by `adb_media_state`.

## Limitations

- `program` is a heuristic: a series whose episodes have no individual title can look like a TV
  programme. That is why it is opt-in.
- Some apps report `playing` already on their home screen (video previews).
- Two ADB clients on one device (this integration plus the built-in `androidtv`) usually coexist;
  if the built-in one starts disconnecting, increase its poll interval or let this integration
  be the only ADB consumer.

## Project status

Small-scope personal integration, maintained for private use and shared as-is: no support
guarantee, no telemetry, no external services. Everything happens on your own network
(ADB to the device, nothing else).

## License

MIT — see [LICENSE](LICENSE).
