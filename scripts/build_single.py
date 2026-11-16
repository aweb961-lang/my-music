"""Make app icons and a single-file build (dist/music.html) with the library and icon inlined.
The single file is what gets published as the Claude artifact.
Run: py scripts/build_library.py && py scripts/build_single.py
"""
import base64, io, json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent

def icon(size):
    s = size * 4
    im = Image.new("RGB", (s, s), "#0e0f13")
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([s*.12, s*.12, s*.88, s*.88], radius=s*.2, fill="#5eead4")
    ink = "#0e0f13"
    # two-note glyph
    d.ellipse([s*.28, s*.56, s*.44, s*.70], fill=ink)
    d.ellipse([s*.54, s*.50, s*.70, s*.64], fill=ink)
    d.rectangle([s*.40, s*.28, s*.44, s*.64], fill=ink)
    d.rectangle([s*.66, s*.22, s*.70, s*.58], fill=ink)
    d.polygon([(s*.40, s*.28), (s*.70, s*.22), (s*.70, s*.32), (s*.40, s*.38)], fill=ink)
    return im.resize((size, size), Image.LANCZOS)

def main():
    icons = ROOT / "icons"; icons.mkdir(exist_ok=True)
    for n in (180, 192, 512):
        icon(n).save(icons / f"icon-{n}.png")
    buf = io.BytesIO(); icon(180).save(buf, "PNG")
    touch = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    html = (ROOT / "index.html").read_text(encoding="utf-8")
    lib = json.loads((ROOT / "data" / "library.json").read_text(encoding="utf-8"))
    libjson = json.dumps(lib, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = html.replace('<link rel="apple-touch-icon" href="icons/icon-180.png">',
                        f'<link rel="apple-touch-icon" href="{touch}">')
    html = html.replace('<link rel="manifest" href="manifest.json">\n', "")
    html = html.replace("<script>\n// ---------- Data",
                        f'<script id="libdata" type="application/json">{libjson}</script>\n<script>\n// ---------- Data', 1)
    # The artifact host wraps the page in its own doctype/head/body, so drop ours.
    for tag in ['<!doctype html>\n', '<html lang="en">\n', '<head>\n', '</head>\n', '<body>\n', '</body>\n', '</html>\n',
                '<meta charset="utf-8">\n',
                '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n']:
        html = html.replace(tag, "", 1)
    title = '<title>My Music</title>\n'
    html = title + html.replace(title, "", 1)
    out = ROOT / "dist"; out.mkdir(exist_ok=True)
    (out / "music.html").write_text(html, encoding="utf-8")
    print(f"dist/music.html {len(html)//1024} KB, {len(lib['tracks'])} songs")

if __name__ == "__main__":
    main()
