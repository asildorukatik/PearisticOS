from __future__ import annotations

import base64
import mimetypes
import re
import sys
from pathlib import Path


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def inline_generated_assets(dist: Path, html: str) -> str:
    script_pattern = re.compile(r'<script(?P<attrs>[^>]*?)\s+src=["\'](?P<src>[^"\']+)["\'](?P<tail>[^>]*)></script>')
    link_pattern = re.compile(r'<link(?P<attrs>[^>]*?)href=["\'](?P<href>[^"\']+)["\'](?P<tail>[^>]*)>')

    def resolve(ref: str) -> Path:
        clean = ref.split("?", 1)[0].split("#", 1)[0]
        clean = clean[2:] if clean.startswith("./") else clean.lstrip("/")
        return dist / clean

    def script_repl(match: re.Match[str]) -> str:
        ref = match.group("src")
        path = resolve(ref)
        if not path.exists() or path.suffix != ".js":
            return match.group(0)
        js = path.read_text(encoding="utf-8")
        # Avoid the outer HTML parser terminating an inline module because an
        # embedded app string happens to contain a literal closing script tag.
        js = js.replace("</script>", "<\\/script>")
        return f'<script type="module">{js}</script>'

    html = script_pattern.sub(script_repl, html)

    def link_repl(match: re.Match[str]) -> str:
        full = match.group(0)
        ref = match.group("href")
        path = resolve(ref)
        if not path.exists():
            return full
        rel_match = re.search(r'rel=["\']([^"\']+)["\']', full)
        rel = rel_match.group(1) if rel_match else ""
        if "stylesheet" in rel and path.suffix == ".css":
            css = path.read_text(encoding="utf-8")
            return f"<style>{css}</style>"
        if path.is_file():
            return full.replace(ref, data_uri(path))
        return full

    return link_pattern.sub(link_repl, html)


def inline_remaining_local_files(dist: Path, html: str) -> str:
    ignored = {"index.html"}
    files = [p for p in dist.rglob("*") if p.is_file() and p.relative_to(dist).as_posix() not in ignored]
    # Longest paths first prevents a shorter path from partially matching a longer one.
    files.sort(key=lambda p: len(p.relative_to(dist).as_posix()), reverse=True)
    for path in files:
        rel = path.relative_to(dist).as_posix()
        if path.suffix in {".js", ".css", ".map"}:
            continue
        uri = data_uri(path)
        for variant in (f"./{rel}", f"/{rel}"):
            html = html.replace(variant, uri)
    return html


def verify_single_file(html: str) -> None:
    """Verify packaging properties that survive Vite/Rollup minification.

    Source-level identity/behavior is already verified by test_source.py before
    Vite runs. Here we verify only the final artifact contract: the generated
    module and stylesheet are embedded and no generated /assets dependency is
    left for file:// to resolve.
    """
    forbidden = [
        r'<script[^>]+src=["\']\.?/assets/',
        r'<link[^>]+href=["\']\.?/assets/',
    ]
    for pattern in forbidden:
        if re.search(pattern, html):
            raise RuntimeError(f"Generated local resource was not inlined: {pattern}")

    inline_modules = re.findall(r'<script\s+type=["\']module["\']>', html)
    if not inline_modules:
        raise RuntimeError("No inline Vite module found in final HTML")

    if len(html.encode("utf-8")) <= 20_000_000:
        raise RuntimeError("Final HTML is too small to contain the embedded PearisticOS payload")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: inline_dist.py <dist-dir> <output-html>")
    dist = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    source = dist / "index.html"
    html = source.read_text(encoding="utf-8")
    html = inline_generated_assets(dist, html)
    html = inline_remaining_local_files(dist, html)
    verify_single_file(html)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    print(f"Wrote {output} ({output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
