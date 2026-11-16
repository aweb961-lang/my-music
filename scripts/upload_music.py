"""Upload new audio files from your music folder to the private R2 bucket.

  py scripts/upload_music.py "C:\\path\\to\\music folder"            # upload new files
  py scripts/upload_music.py "C:\\path\\to\\music folder" --dry-run  # just show what matches

Uses Wrangler (needs Node and a one-time `npx wrangler login`). Already-uploaded files are
remembered in cloud/uploaded.json and skipped.
"""
import json, subprocess, sys
from pathlib import Path
from music_files import ROOT, match_folder

BUCKET = "my-music"
DONE = ROOT / "cloud" / "uploaded.json"

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    folder, dry = sys.argv[1], "--dry-run" in sys.argv
    done = json.loads(DONE.read_text()) if DONE.exists() else {}
    files = match_folder(folder)
    matched = sum(1 for f in files if f["song"])
    print(f"{len(files)} audio files: {matched} match your library, {len(files) - matched} go to 'extra' (genre Other).")
    for f in files:
        sig = f"{f['path'].stat().st_size}:{int(f['path'].stat().st_mtime)}"
        if done.get(f["key"]) == sig:
            continue
        label = f"{f['song']['artist']} - {f['song']['title']}" if f["song"] else f"(extra) {f['path'].name}"
        print(("would upload " if dry else "uploading ") + label)
        if dry:
            continue
        cmd = ["npx", "--yes", "wrangler@4", "r2", "object", "put", f"{BUCKET}/{f['key']}",
               "--file", str(f["path"]), "--content-type", f["type"], "--remote"]
        r = subprocess.run(cmd, cwd=ROOT / "cloud", shell=True, capture_output=True, text=True)
        if r.returncode != 0:
            print("  failed:", (r.stderr or r.stdout).strip().splitlines()[-1:])
            continue
        done[f["key"]] = sig
        DONE.write_text(json.dumps(done, indent=1))
    print("done.")

if __name__ == "__main__":
    main()
