"""Build data/library.json from the playlist text files in data/playlists/.

Each file: lines "Title|Artist, Artist". "@playlist <name> <default-genre>" starts a playlist
inside a file; otherwise the file name is the playlist and the "default genre X" header sets the genre.
ARTIST_GENRE overrides the playlist default (e.g. Eminem in the lifting playlist -> hiphop).
Run: py scripts/build_library.py
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "playlists"
OUT = ROOT / "data" / "library.json"

GENRES = ["country", "pop", "rock", "worship", "hiphop", "electronic"]

ARTIST_GENRE = {
    # hip-hop / rap
    "eminem": "hiphop", "metro boomin": "hiphop", "ryan caraveo": "hiphop", "neffex": "hiphop",
    "blackbear": "hiphop", "juice wrld": "hiphop", "vin jay": "hiphop", "connor price": "hiphop",
    # electronic / dance
    "swedish house mafia": "electronic", "alan walker": "electronic", "axwell λ ingrosso": "electronic",
    "morgan page": "electronic", "vicetone": "electronic", "kygo": "electronic", "k-391": "electronic",
    "bryan v": "electronic", "gabry ponte": "electronic",
    # rock
    "alice cooper": "rock", "breaking benjamin": "rock", "shinedown": "rock", "bad wolves": "rock",
    "hollywood undead": "rock", "lifehouse": "rock",
    # pop in a rock playlist
    "rihanna": "pop", "tal bachman": "pop", "the cab": "pop",
    # christian
    "tobymac": "worship", "the afters": "worship",
    # country outside the country playlist
    "shaboozey": "country",
}

def key(title, artist):
    t = re.sub(r"\s*[\(\[](feat|with|ft)\.?[^\)\]]*[\)\]]", "", title, flags=re.I)
    t = re.sub(r"\s*\((live|radio edit|re-recorded)[^)]*\)", "", t, flags=re.I)
    return re.sub(r"[^a-z0-9]", "", t.lower()) + "|" + re.sub(r"[^a-z0-9]", "", artist.split(",")[0].lower())

def main():
    tracks, playlists = {}, {}
    for f in sorted(SRC.glob("*.txt")):
        source = "spotify" if f.name.startswith("spotify") else "ytmusic"
        pl = f.stem.split("-", 1)[1].title()
        m = re.search(r"default genre (\w+)", f.read_text(encoding="utf-8").splitlines()[0])
        default = m.group(1) if m else "pop"
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("@playlist"):
                _, pl, default = line.split()
                continue
            title, artist = [x.strip() for x in line.split("|", 1)]
            k = key(title, artist)
            genre = ARTIST_GENRE.get(artist.split(",")[0].strip().lower(), default)
            if source == "spotify":
                genre = "country"
            t = tracks.setdefault(k, {"id": re.sub(r"[^a-z0-9|]", "", k).replace("|", "--"),
                                      "title": title, "artist": artist, "genre": genre,
                                      "playlists": [], "source": source})
            if pl not in t["playlists"]:
                t["playlists"].append(pl)
            playlists.setdefault(pl, {"name": pl, "source": source, "trackIds": []})
            if t["id"] not in playlists[pl]["trackIds"]:
                playlists[pl]["trackIds"].append(t["id"])
    lib = {"genres": GENRES, "tracks": sorted(tracks.values(), key=lambda t: (t["genre"], t["artist"].lower())),
           "playlists": list(playlists.values())}
    OUT.write_text(json.dumps(lib, indent=1, ensure_ascii=False), encoding="utf-8")
    counts = {g: sum(t["genre"] == g for t in tracks.values()) for g in GENRES}
    print(f"{len(tracks)} unique songs, {len(playlists)} playlists -> {OUT.relative_to(ROOT)}")
    print(counts)
    artists = {}
    for t in tracks.values():
        a = t["artist"].split(",")[0].strip()
        artists[a] = artists.get(a, 0) + 1
    print("top artists:", sorted(artists.items(), key=lambda x: -x[1])[:25])

if __name__ == "__main__":
    main()
