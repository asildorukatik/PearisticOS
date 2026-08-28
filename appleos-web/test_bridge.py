from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

TARGET = Path(__file__).parent / "bridge" / "appleos_bridge.py"


def load_bridge():
    if not TARGET.exists():
        raise FileNotFoundError(TARGET)
    spec = importlib.util.spec_from_file_location("appleos_bridge", TARGET)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.bridge = load_bridge()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write_desktop(self, name: str, body: str) -> Path:
        path = self.root / name
        path.write_text(body, encoding="utf-8")
        return path

    def test_parse_application_is_sanitized(self):
        path = self.write_desktop(
            "demo.desktop",
            "[Desktop Entry]\nType=Application\nName=Demo App\nIcon=demo-icon\nCategories=Utility;Development;\nExec=demo --danger %U\n",
        )
        item = self.bridge.parse_desktop_file(path)
        self.assertEqual(item["id"], "demo.desktop")
        self.assertEqual(item["name"], "Demo App")
        self.assertEqual(item["icon"], "demo-icon")
        self.assertEqual(item["categories"], ["Utility", "Development"])
        self.assertNotIn("Exec", item)
        self.assertNotIn("exec", item)
        self.assertEqual(item["_path"], str(path))

    def test_hidden_and_no_display_entries_are_ignored(self):
        hidden = self.write_desktop(
            "hidden.desktop",
            "[Desktop Entry]\nType=Application\nName=Hidden\nHidden=true\nExec=hidden\n",
        )
        nodisplay = self.write_desktop(
            "nodisplay.desktop",
            "[Desktop Entry]\nType=Application\nName=NoDisplay\nNoDisplay=true\nExec=nodisplay\n",
        )
        self.assertIsNone(self.bridge.parse_desktop_file(hidden))
        self.assertIsNone(self.bridge.parse_desktop_file(nodisplay))

    def test_non_application_entries_are_ignored(self):
        path = self.write_desktop(
            "link.desktop",
            "[Desktop Entry]\nType=Link\nName=Website\nURL=https://example.com\n",
        )
        self.assertIsNone(self.bridge.parse_desktop_file(path))

    def test_desktop_id_validation_rejects_path_traversal(self):
        self.assertTrue(self.bridge.valid_desktop_id("org.example.App.desktop"))
        for bad in ["../x.desktop", "/tmp/x.desktop", "x/y.desktop", "x.desktop;rm", "x"]:
            self.assertFalse(self.bridge.valid_desktop_id(bad), bad)

    def test_scan_returns_public_metadata_only(self):
        self.write_desktop(
            "demo.desktop",
            "[Desktop Entry]\nType=Application\nName=Demo App\nIcon=demo\nExec=demo --secret\n",
        )
        public, internal = self.bridge.scan_applications([self.root])
        self.assertEqual(len(public), 1)
        self.assertEqual(public[0]["id"], "demo.desktop")
        self.assertNotIn("_path", public[0])
        self.assertNotIn("Exec", public[0])
        self.assertEqual(internal["demo.desktop"], str(self.root / "demo.desktop"))

    def test_authorization_uses_bearer_token(self):
        self.assertTrue(self.bridge.authorized("Bearer abc123", "abc123"))
        self.assertFalse(self.bridge.authorized("Bearer wrong", "abc123"))
        self.assertFalse(self.bridge.authorized(None, "abc123"))

    def test_launch_uses_gio_without_shell(self):
        path = self.write_desktop(
            "demo.desktop",
            "[Desktop Entry]\nType=Application\nName=Demo\nExec=demo\n",
        )
        calls = []

        def runner(args):
            calls.append(args)
            return object()

        self.bridge.launch_application("demo.desktop", {"demo.desktop": str(path)}, runner=runner)
        self.assertEqual(calls, [["gio", "launch", str(path)]])

    def test_unknown_launch_is_rejected(self):
        with self.assertRaises(KeyError):
            self.bridge.launch_application("missing.desktop", {}, runner=lambda args: None)

    def test_bridge_is_loopback_only(self):
        self.assertEqual(self.bridge.HOST, "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
