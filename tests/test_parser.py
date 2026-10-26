"""Parser tests built on real `dumpsys media_session` captures.

Run with:  python -m unittest discover -s tests -v
(no third-party dependencies required)
"""
from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "custom_components" / "adb_media_state"))

from parser import classify, parse_session  # noqa: E402

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"

# (fixture, expected mode without program detection, expected with it)
CASES = [
    ("serial-vod.txt", "vod", "vod"),
    ("film-vod.txt", "vod", "vod"),
    ("live-channel.txt", "live", "live"),
    ("program-vod.txt", "vod", "program"),
    ("program-vod-2.txt", "vod", "program"),
    ("idle.txt", "idle", "idle"),
]

PACKAGE = "com.wbd.stream"


def load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class ParserTest(unittest.TestCase):
    def test_modes_without_program_detection(self) -> None:
        for fixture, expected, _ in CASES:
            with self.subTest(fixture=fixture):
                session = parse_session(load(fixture), PACKAGE)
                self.assertEqual(classify(session, False), expected)

    def test_modes_with_program_detection(self) -> None:
        for fixture, _, expected in CASES:
            with self.subTest(fixture=fixture):
                session = parse_session(load(fixture), PACKAGE)
                self.assertEqual(classify(session, True), expected)

    def test_metadata_fields(self) -> None:
        session = parse_session(load("serial-vod.txt"), PACKAGE)
        assert session is not None
        self.assertEqual(session.title, "Ziemia i gwiazdy")
        self.assertEqual(session.subtitle, "Latarnie")
        self.assertEqual(session.speed, 1.0)
        self.assertGreater(session.position or 0, 0)

    def test_live_signals(self) -> None:
        session = parse_session(load("live-channel.txt"), PACKAGE)
        assert session is not None
        self.assertLess(session.position or 0, 0)
        self.assertEqual(session.speed, 0.0)

    def test_missing_package_returns_none(self) -> None:
        self.assertIsNone(parse_session(load("serial-vod.txt"), "com.example.absent"))

    def test_any_package_mode(self) -> None:
        session = parse_session(load("film-vod.txt"), None)
        assert session is not None
        self.assertEqual(session.package, PACKAGE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
