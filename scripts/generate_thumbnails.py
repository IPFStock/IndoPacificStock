#!/usr/bin/env python3
"""Extract JPEG posters from GitHub-hosted preview MP4s into thumbs/."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "videos" / "catalog.json"
THUMBS_DIR = ROOT / "thumbs"
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"


def jobs_from_catalog() -> list[tuple[str, str]]:
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    jobs = []
    for clip in data.get("clips") or []:
        slug = clip.get("slug") or (clip.get("technicalSpecs") or {}).get("slug")
        url = clip.get("videoUrl")
        if slug and url:
            jobs.append((slug, url))
    return jobs


def extract_one(slug: str, url: str, dest: Path, seek: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".tmp.jpg")
    cmd = [
        FFMPEG,
        "-hide_banner",
        "-loglevel",
        "error",
        "-user_agent",
        "IPFStock-thumbs/1.0",
        "-ss",
        seek,
        "-i",
        url,
        "-frames:v",
        "1",
        "-vf",
        "scale=1280:-2",
        "-q:v",
        "5",
        "-y",
        str(tmp),
    ]
    subprocess.run(cmd, check=True, timeout=60, capture_output=True)
    if not tmp.exists() or tmp.stat().st_size < 2000:
        tmp.unlink(missing_ok=True)
        raise RuntimeError("empty or tiny JPEG")
    tmp.replace(dest)


def process(slug: str, url: str, force: bool) -> str:
    dest = THUMBS_DIR / f"{slug}.jpg"
    if dest.exists() and dest.stat().st_size > 2000 and not force:
        return "skip"
    try:
        extract_one(slug, url, dest, "1")
        return "ok"
    except Exception:
        try:
            extract_one(slug, url, dest, "0")
            return "ok-fallback"
        except Exception as err:
            return f"fail:{err}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    if not Path(FFMPEG).exists():
        raise SystemExit("ffmpeg not found")

    jobs = jobs_from_catalog()
    if args.limit:
        jobs = jobs[: args.limit]
    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Extracting thumbnails for {len(jobs)} clips → {THUMBS_DIR}/", flush=True)

    ok = skip = fail = 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {
            pool.submit(process, slug, url, args.force): slug for slug, url in jobs
        }
        done = 0
        for future in as_completed(futures):
            slug = futures[future]
            done += 1
            result = future.result()
            if result == "skip":
                skip += 1
            elif result.startswith("fail"):
                fail += 1
                print(f"  FAIL {slug}: {result[5:200]}", flush=True)
            else:
                ok += 1
            if done % 25 == 0 or done == len(jobs):
                print(f"  {done}/{len(jobs)}  ok={ok} skip={skip} fail={fail}", flush=True)

    print(f"Done. ok={ok} skipped={skip} failed={fail}", flush=True)
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
