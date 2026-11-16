"""Shared helper: match audio files in a folder to songs in data/library.json and give each its cloud key.

Name files "Artist - Title.mp3" (m4a/aac/ogg/opus/wav/flac also work).
Matched songs -> tracks/<library id>.<ext>; anything else -> extra/<file name>.
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIO = {".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".flac"}
TYPES = {".mp3": "audio/mpeg", ".m4a": "audio/mp4", ".aac": "audio/aac", ".ogg": "audio/ogg",
         ".opus": "audio/ogg", ".wav": "audio/wav", ".flac": "audio/flac"}

def norm(s):
    s = re.sub(r"\s*[\(\[](feat|ft|with)[^\)\]]*[\)\]]", "", s.lower())
    return re.sub(r"[^a-z0-9]", "", s)

def library():
    return json.loads((ROOT / "data" / "library.json").read_text(encoding="utf-8"))["tracks"]

def match_folder(folder):
    tracks = library()
    out = []
    for f in sorted(Path(folder).rglob("*")):
        if f.suffix.lower() not in AUDIO:
            continue
        base = f.stem
        artist, title = base.split(" - ", 1) if " - " in base else ("", base)
        a0 = norm(artist.split(",")[0])
        hit = next((t for t in tracks if norm(t["title"]) == norm(title) and a0 and norm(t["artist"]).startswith(a0)), None) \
            or next((t for t in tracks if norm(t["title"]) == norm(title) and not a0), None)
        ext = f.suffix.lower()
        key = f"tracks/{hit['id']}{ext}" if hit else f"extra/{base}{ext}"
        out.append({"path": f, "key": key, "song": hit, "type": TYPES[ext]})
    return out
