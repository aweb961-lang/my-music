"""Write data/songs.csv: artist, title, YouTube link to the audio-only (album track) version.

Input: data/youtube_links.json  {library id: {vid, ytTitle, ytSub, match}} from the YouTube Music
"Songs" search (album tracks from "Artist - Topic" channels, not music videos).
Run: py scripts/make_csv.py
"""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    lib = json.loads((ROOT / "data" / "library.json").read_text(encoding="utf-8"))["tracks"]
    links = json.loads((ROOT / "data" / "youtube_links.json").read_text(encoding="utf-8"))
    out = ROOT / "data" / "songs.csv"
    counts = {}
    with out.open("w", newline="", encoding="utf-8-sig") as f:   # utf-8-sig so Excel shows accents right
        w = csv.writer(f)
        w.writerow(["Artist", "Title", "Genre", "YouTube (audio only)", "Match"])
        for t in sorted(lib, key=lambda t: (t["genre"], t["artist"].lower(), t["title"].lower())):
            r = links.get(t["id"], {})
            vid = r.get("vid", "")
            match = r.get("match", "none")
            counts[match] = counts.get(match, 0) + 1
            w.writerow([t["artist"], t["title"], t["genre"],
                        f"https://music.youtube.com/watch?v={vid}" if vid else "",
                        {"exact": "exact", "close": "close - check", "check": "CHECK", "none": "NOT FOUND"}[match]])
    print(f"wrote {out.relative_to(ROOT)}: {len(lib)} songs", counts)

if __name__ == "__main__":
    main()
