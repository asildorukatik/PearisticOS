from __future__ import annotations

import base64
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("inline_dist.py")


class InlineDistTests(unittest.TestCase):
    def make_dist(self, html: str):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / "assets").mkdir()
        (root / "index.html").write_text(html, encoding="utf-8")
        return temp, root

    def pack(self, root: Path):
        output = root / "packed.html"
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), str(root), str(output)],
            text=True,
            capture_output=True,
        )
        return proc, output

    def test_inlines_vite_tags_regardless_of_attribute_order_and_css_assets(self):
        temp, root = self.make_dist(
            '<!doctype html><link href="./assets/app.css" rel="stylesheet">'
            '<script src="./assets/app.js" crossorigin type="module"></script>'
        )
        self.addCleanup(temp.cleanup)
        (root / "assets/app.js").write_text('console.log("ok")', encoding="utf-8")
        (root / "assets/icon.png").write_bytes(b"PNGDATA")
        (root / "assets/app.css").write_text('.x{background:url("./icon.png")}', encoding="utf-8")

        proc, output = self.pack(root)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        text = output.read_text(encoding="utf-8")
        encoded = base64.b64encode(b"PNGDATA").decode("ascii")
        self.assertIn('console.log("ok")', text)
        self.assertIn("data:image/png;base64," + encoded, text)
        self.assertNotIn("assets/app.js", text)
        self.assertNotIn("assets/app.css", text)
        self.assertNotIn("./icon.png", text)

    def test_keeps_external_and_data_urls_untouched(self):
        temp, root = self.make_dist(
            '<link rel="stylesheet" href="https://example.com/x.css">'
            '<img src="data:image/png;base64,AA==">'
        )
        self.addCleanup(temp.cleanup)
        proc, output = self.pack(root)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        text = output.read_text(encoding="utf-8")
        self.assertIn("https://example.com/x.css", text)
        self.assertIn("data:image/png;base64,AA==", text)


if __name__ == "__main__":
    unittest.main()
