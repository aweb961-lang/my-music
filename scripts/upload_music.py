"""Upload new audio files from your music folder to the private R2 bucket.

  py scripts/upload_music.py "C:\\path\\to\\music folder"            # upload new files
  py scripts/upload_music.py "C:\\path\\to\\music folder" --dry-run  # just show what matches

Uses the project's Wrangler (cloud/wrangler.cmd). Already-uploaded files are remembered in
cloud/uploaded.json and skipped.

Guardrail: refuses to upload anything that would take the bucket past LIMIT_GB (R2's free tier is 10 GB),
using the live bucket size from the streaming server (cloud/worker-url.txt + cloud/access-key.txt).
"""
import json, subprocess, sys, urllib.request, urllib.parse
from pathlib import Path
from music_files import ROOT, match_folder

BUCKET = "my-music"
LIMIT_GB = 9.0
CLOUD = ROOT / "cloud"
DONE = CLOUD / "uploaded.json"

def bucket_bytes():
    """Live size of the bucket via the Worker's /index. Falls back to what this script has uploaded."""
    try:
        url = (CLOUD / "worker-url.txt").read_text().strip()
        key = (CLOUD / "access-key.txt").read_text().strip()
        with urllib.request.urlopen(f"{url}/index?k={urllib.parse.quote(key)}", timeout=20) as r:
            return sum(f["size"] for f in json.load(r)["files"]), "live"
    except Exception:
        done = json.loads(DONE.read_text()) if DONE.exists() else {}
        return sum(int(v.split(":")[0]) for v in done.values()), "local record"

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    folder, dry = sys.argv[1], "--dry-run" in sys.argv
    done = json.loads(DONE.read_text()) if DONE.exists() else {}
    files = match_folder(folder)
    matched = sum(1 for f in files if f["song"])
    print(f"{len(files)} audio files: {matched} match your library, {len(files) - matched} go to 'extra' (genre Other).")

    todo = []
    for f in files:
        st = f["path"].stat()
        f["sig"] = f"{st.st_size}:{int(st.st_mtime)}"
        if done.get(f["key"]) != f["sig"]:
            todo.append(f)
    used, source = bucket_bytes()
    new = sum(f["path"].stat().st_size for f in todo)
    limit = LIMIT_GB * 1024**3
    print(f"Bucket now {used/1024**3:.2f} GB ({source}); {len(todo)} new files add {new/1024**3:.2f} GB; limit {LIMIT_GB:.0f} GB.")
    if used + new > limit:
        sys.exit(f"Stopped: that would pass {LIMIT_GB:.0f} GB and could start R2 charges. Remove files or raise LIMIT_GB on purpose.")

    for f in todo:
        label = f"{f['song']['artist']} - {f['song']['title']}" if f["song"] else f"(extra) {f['path'].name}"
        print(("would upload " if dry else "uploading ") + label)
        if dry:
            continue
        cmd = [str(CLOUD / "wrangler.cmd"), "r2", "object", "put", f"{BUCKET}/{f['key']}",
               "--file", str(f["path"]), "--content-type", f["type"], "--remote"]
        r = subprocess.run(cmd, cwd=CLOUD, capture_output=True, text=True)
        if r.returncode != 0:
            print("  failed:", (r.stderr or r.stdout).strip().splitlines()[-1:])
            continue
        done[f["key"]] = f["sig"]
        DONE.write_text(json.dumps(done, indent=1))
    print("done.")

if __name__ == "__main__":
    main()
