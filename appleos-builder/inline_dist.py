#!/usr/bin/env python3
from __future__ import annotations

import base64
import mimetypes
import re
import sys
from pathlib import Path
from urllib.parse import unquote

TAG_RE = re.compile(r'<(?P<tag>link|script)\b(?P<attrs>[^>]*)>(?P<close></script>)?', re.I)
ATTR_RE = re.compile(r'([:\w-]+)(?:\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+)))?')
CSS_URL_RE = re.compile(r'url\(\s*(["\']?)([^"\')]+)\1\s*\)', re.I)


def attrs_dict(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in ATTR_RE.finditer(raw):
        out[match.group(1).lower()] = match.group(2) or match.group(3) or match.group(4) or ""
    return out


def is_external(url: str) -> bool:
    value = url.strip().lower()
    return value.startswith(("http://", "https://", "data:", "blob:", "//", "#"))


def resolve_asset(dist: Path, url: str, base_dir: Path | None = None) -> Path:
    cleaned = unquote(url.split("?", 1)[0].split("#", 1)[0])
    if cleaned.startswith("/"):
        path = dist / cleaned.lstrip("/")
    else:
        path = (base_dir or dist) / cleaned
    path = path.resolve()
    path.relative_to(dist.resolve())
    if not path.exists():
        raise SystemExit(f"referenced build asset does not exist: {url}")
    return path


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def inline_css_urls(css: str, css_path: Path, dist: Path) -> str:
    def replace(match: re.Match[str]) -> str:
        url = match.group(2).strip()
        if is_external(url):
            return match.group(0)
        asset = resolve_asset(dist, url, css_path.parent)
        return f'url("{data_uri(asset)}")'

    return CSS_URL_RE.sub(replace, css)


def inline_tags(html: str, dist: Path) -> str:
    def replace(match: re.Match[str]) -> str:
        tag = match.group("tag").lower()
        attrs = attrs_dict(match.group("attrs"))
        if tag == "link" and attrs.get("rel", "").lower() == "stylesheet" and attrs.get("href") and not is_external(attrs["href"]):
            css_path = resolve_asset(dist, attrs["href"])
            css = inline_css_urls(css_path.read_text(encoding="utf-8"), css_path, dist)
            return "<style>\n" + css + "\n</style>"
        if tag == "script" and attrs.get("src") and attrs.get("type", "").lower() == "module" and not is_external(attrs["src"]):
            js_path = resolve_asset(dist, attrs["src"])
            js = js_path.read_text(encoding="utf-8")
            return '<script type="module">\n' + js + "\n</script>"
        return match.group(0)

    return TAG_RE.sub(replace, html)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: inline_dist.py <dist-dir> <output.html>")

    dist = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    html = (dist / "index.html").read_text(encoding="utf-8")
    html = inline_tags(html, dist)

    leftovers = re.findall(r'(?:src|href)=["\'](?:\.?/)?assets/', html, re.I)
    if leftovers:
        raise SystemExit("self-contained pack still references local assets")

    output.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
