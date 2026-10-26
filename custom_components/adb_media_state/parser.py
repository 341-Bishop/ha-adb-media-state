"""Parse `dumpsys media_session` output and classify playback mode.

Modes:
    idle    - no session, or session stopped/errored
    live    - playing/paused with position < 0 or speed == 0 (linear stream)
    program - VOD whose metadata fields 1 and 2 are identical (experimental heuristic,
              only reported when `detect_program` is enabled)
    vod     - any other on-demand playback
"""
from __future__ import annotations

import re
from dataclasses import dataclass

IGNORED_PACKAGES = ("com.android.bluetooth",)

_SESSION_START = re.compile(r"\n\s*(?=package=)")
_BLOCK_END = re.compile(r"\n\s*(?:Audio playback|Media session config)")
_PACKAGE = re.compile(r"\s*package=(\S+)")


@dataclass
class SessionInfo:
    """Single media session, as far as we can see it."""

    package: str = ""
    state: str = "UNKNOWN"
    position: int | None = None
    speed: float | None = None
    actions: int | None = None
    title: str = ""
    subtitle: str = ""
    album: str = ""


def _clean(value: str | None) -> str:
    if value is None or value in ("null", "None"):
        return ""
    return value.strip()


def _blocks(dump: str) -> list[tuple[str, str]]:
    """Split a dumpsys report into (package, block) pairs."""
    result: list[tuple[str, str]] = []
    for chunk in _SESSION_START.split(dump):
        match = _PACKAGE.match(chunk)
        if not match:
            continue
        body = chunk
        cut = _BLOCK_END.search(body)
        if cut:
            body = body[: cut.start()]
        result.append((match.group(1), body))
    return result


def parse_session(dump: str, package: str | None = None) -> SessionInfo | None:
    """Return the session of interest, or None when there is none.

    When ``package`` is empty, the first session that actually holds playback
    state (and is not a known system stub such as the Bluetooth stack) is used.
    """
    blocks = _blocks(dump)
    chosen: tuple[str, str] | None = None

    if package:
        for pkg, body in blocks:
            if pkg == package:
                chosen = (pkg, body)
                break
    else:
        for pkg, body in blocks:
            if pkg in IGNORED_PACKAGES:
                continue
            if "state=PlaybackState" in body:
                chosen = (pkg, body)
                break

    if chosen is None:
        return None

    pkg, body = chosen
    state = re.search(r"state=PlaybackState \{state=(\w+)\(", body)
    position = re.search(r"position=(-?\d+)", body)
    speed = re.search(r"speed=(-?[\d.]+)", body)
    actions = re.search(r"actions=(\d+)", body)
    meta = re.search(r"metadata: size=\d+, description=([^\n]*)", body)

    title = subtitle = album = ""
    if meta:
        parts = [p.strip() for p in meta.group(1).split(",")]
        title = _clean(parts[0] if parts else "")
        subtitle = _clean(parts[1] if len(parts) > 1 else "")
        album = _clean(parts[2] if len(parts) > 2 else "")

    return SessionInfo(
        package=pkg,
        state=state.group(1) if state else "UNKNOWN",
        position=int(position.group(1)) if position else None,
        speed=float(speed.group(1)) if speed else None,
        actions=int(actions.group(1)) if actions else None,
        title=title,
        subtitle=subtitle,
        album=album,
    )


def classify(session: SessionInfo | None, detect_program: bool = False) -> str:
    """Turn a session into one of: idle, live, program, vod."""
    if session is None:
        return "idle"
    if session.state in ("STOPPED", "ERROR", "NONE", "UNKNOWN"):
        return "idle"

    if (session.position is not None and session.position < 0) or session.speed == 0.0:
        return "live"

    if detect_program:
        title = (session.title or "").strip().lower()
        subtitle = (session.subtitle or "").strip().lower()
        if subtitle and subtitle == title:
            return "program"

    return "vod"
