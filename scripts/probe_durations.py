#!/usr/bin/env python3
"""Probe preview MP4 durations from GitHub and write them into catalog JSON.

By default every clip is probed so the site shows the preview file length,
not the DaVinci / CSV master Duration TC. Empty CSV Duration TC cells are
filled when missing; existing master durations are left alone.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import struct
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIDEOS_DIR = ROOT / 'videos'
MASTER_CSV = ROOT / 'Raja Stock Clips 3 Clips Metadata.csv'
GITHUB_RAW = 'https://raw.githubusercontent.com/IPFStock/ip-assets-01/main'
TAIL_BYTES = 4 * 1024 * 1024
USER_AGENT = 'IPFStock-duration-probe/1.0'
PREVIEW_SOURCES = {'mp4-probe', 'ffprobe'}
WORKERS = 8


SKIP_JSON = {'catalog.json', 'manifest.json', 'homepage-featured.json'}


def parse_fps(raw: str) -> float:
    if not raw:
        return 0.0
    value = str(raw).strip()
    if '/' in value:
        num, den = value.split('/', 1)
        try:
            fps = float(num) / float(den)
            return fps if fps > 0 else 0.0
        except ValueError:
            return 0.0
    try:
        fps = float(value)
        return fps if fps > 0 else 0.0
    except ValueError:
        return 0.0


def infer_fps(file_name: str, spec: dict) -> float:
    parsed = parse_fps(spec.get('fps', ''))
    if parsed >= 18:
        return parsed
    prefix = (file_name or '').upper()[:4]
    if prefix == 'A002':
        return 48.0
    return 50.0


def format_duration_smpte(total_seconds: float, fps: float) -> str:
    frame_rate = max(1, round(parse_fps(str(fps))))
    total_frames = max(0, round(total_seconds * frame_rate))
    frame_count = total_frames % frame_rate
    total_seconds_int = total_frames // frame_rate
    hours = total_seconds_int // 3600
    minutes = (total_seconds_int % 3600) // 60
    seconds = total_seconds_int % 60
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}:{frame_count:02d}'


def fetch_range(url: str, start: int, end: int) -> bytes:
    req = urllib.request.Request(
        url,
        headers={'Range': f'bytes={start}-{end}', 'User-Agent': USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read()


def file_size(url: str) -> int:
    req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as response:
        return int(response.headers['Content-Length'])


def parse_mvhd(atom: bytes) -> float | None:
    if len(atom) < 28:
        return None
    version = atom[8]
    if version == 0:
        timescale = struct.unpack('>I', atom[20:24])[0]
        duration = struct.unpack('>I', atom[24:28])[0]
    else:
        if len(atom) < 40:
            return None
        timescale = struct.unpack('>I', atom[28:32])[0]
        duration = struct.unpack('>Q', atom[32:40])[0]
    if not timescale:
        return None
    return duration / timescale


def find_atom(data: bytes, atom_type: bytes, start: int = 0) -> bytes | None:
    pos = start
    while pos + 8 <= len(data):
        size = struct.unpack('>I', data[pos:pos + 4])[0]
        atype = data[pos + 4:pos + 8]
        header = 8
        if size == 1 and pos + 16 <= len(data):
            size = struct.unpack('>Q', data[pos + 8:pos + 16])[0]
            atype = data[pos + 16:pos + 20]
            header = 16
        if size < header:
            break
        end = min(len(data), pos + size)
        if atype == atom_type:
            return data[pos:end]
        if atype in {b'moov', b'trak', b'mdia', b'minf', b'stbl', b'edts', b'mvex'}:
            found = find_atom(data[pos + header:end], atom_type)
            if found:
                return found
        pos += size
    return None


def find_mvhd_by_scan(data: bytes) -> bytes | None:
    pos = 0
    while True:
        idx = data.find(b'mvhd', pos)
        if idx < 4:
            return None
        size = struct.unpack('>I', data[idx - 4:idx])[0]
        end = idx - 4 + size
        if 32 <= size <= 256 and end <= len(data) and data[idx:idx + 4] == b'mvhd':
            return data[idx - 4:end]
        pos = idx + 4


def locate_mvhd(data: bytes) -> bytes | None:
    return find_atom(data, b'mvhd') or find_mvhd_by_scan(data)


def probe_mp4_duration(url: str) -> float | None:
    size = file_size(url)
    if size <= 0:
        return None

    start = max(0, size - TAIL_BYTES)
    data = fetch_range(url, start, size - 1)

    mvhd = locate_mvhd(data)
    if not mvhd:
        head = fetch_range(url, 0, min(size - 1, TAIL_BYTES))
        mvhd = locate_mvhd(head)
    if not mvhd:
        return None
    return parse_mvhd(mvhd)


def reel_base_source(name: str) -> str:
    n = re.sub(r'\.(r3d|mp4|mov)$', '', name, flags=re.I)
    n = re.sub(r'_V\d+-\d+$', '', n, flags=re.I)
    n = re.sub(r'_\d{3}$', '', n)
    return n.upper()


def load_master_rows() -> tuple[list[str], list[list[str]], dict[str, int]]:
    rows = list(csv.reader(MASTER_CSV.read_text(encoding='utf-8-sig').splitlines()))
    header = rows[0]
    width = len(header)
    data = [(row + [''] * width)[:width] for row in rows[1:]]
    idx = {name.strip(): i for i, name in enumerate(header)}
    return header, data, idx


def save_master_rows(header: list[str], data: list[list[str]]) -> None:
    with MASTER_CSV.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(data)


def collect_targets(only_missing: bool) -> list[tuple[Path, dict, str]]:
    targets = []
    for path in sorted(VIDEOS_DIR.glob('*.json')):
        if path.name in SKIP_JSON:
            continue
        payload = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(payload, dict):
            continue
        spec = payload.get('technicalSpecs') or {}
        file_name = spec.get('fileName') or ''
        if not file_name:
            continue
        if only_missing:
            has_preview = str(spec.get('durationSource') or '') in PREVIEW_SOURCES
            has_seconds = float(spec.get('durationSeconds') or 0) > 0
            if has_preview and has_seconds:
                continue
        targets.append((path, payload, file_name))
    return targets


def apply_preview_duration(payload: dict, seconds: float) -> None:
    spec = payload.setdefault('technicalSpecs', {})
    fps = infer_fps(spec.get('fileName') or '', spec)
    smpte = format_duration_smpte(seconds, fps)
    previous = str(spec.get('duration') or '').strip()
    previous_source = str(spec.get('durationSource') or '').strip()
    if previous and previous_source not in PREVIEW_SOURCES and not spec.get('masterDuration'):
        spec['masterDuration'] = previous
    spec['duration'] = smpte
    spec['durationSeconds'] = round(seconds, 3)
    spec['durationSource'] = 'mp4-probe'


def rebuild_catalog() -> int:
    clips = []
    for path in sorted(VIDEOS_DIR.glob('*.json')):
        if path.name in SKIP_JSON:
            continue
        payload = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(payload, dict):
            continue
        clips.append({'slug': path.stem, **payload})
    clips.sort(key=lambda clip: (clip.get('title') or '').lower())
    bundle = {
        'version': len(clips),
        'generatedAt': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'clips': clips,
    }
    (VIDEOS_DIR / 'catalog.json').write_text(json.dumps(bundle), encoding='utf-8')
    return len(clips)


def probe_one(path: Path, payload: dict, file_name: str) -> tuple[str, float | None, str]:
    url = payload.get('videoUrl') or f'{GITHUB_RAW}/{file_name}'
    label = payload.get('title') or path.stem
    seconds = probe_mp4_duration(url)
    return label, seconds, file_name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--only-missing',
        action='store_true',
        help='Only probe clips that do not already have a preview MP4 duration',
    )
    args = parser.parse_args()

    targets = collect_targets(args.only_missing)
    if not targets:
        print('No clips need duration probing.')
        return 0

    print(f'Probing {len(targets)} preview MP4s…')
    header, master_data, idx = load_master_rows()
    duration_idx = idx.get('Duration TC', -1)
    file_idx = idx.get('File Name', -1)
    master_by_mp4 = {}
    master_by_base = {}
    if file_idx >= 0:
        for row in master_data:
            fn = row[file_idx].strip()
            if not fn:
                continue
            master_by_mp4[fn.lower()] = row
            master_by_base[reel_base_source(fn)] = row

    probed = 0
    failed = 0
    csv_filled = False

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {
            pool.submit(probe_one, path, payload, file_name): (path, payload, file_name)
            for path, payload, file_name in targets
        }
        for future in as_completed(futures):
            path, payload, file_name = futures[future]
            label = payload.get('title') or path.stem
            try:
                _, seconds, _ = future.result()
                if not seconds or seconds <= 0:
                    print(f'  FAIL {label}: no duration from MP4')
                    failed += 1
                    continue
                apply_preview_duration(payload, seconds)
                path.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')

                spec = payload['technicalSpecs']
                if duration_idx >= 0:
                    row = master_by_mp4.get(file_name.lower())
                    if row is None:
                        row = master_by_base.get(reel_base_source(file_name))
                    if row is not None and not row[duration_idx].strip():
                        row[duration_idx] = spec['duration']
                        csv_filled = True

                print(f'  OK {label}: {spec["duration"]} ({seconds:.2f}s)')
                probed += 1
            except (urllib.error.URLError, TimeoutError, ValueError, struct.error, OSError) as err:
                print(f'  FAIL {label}: {err}')
                failed += 1

    if csv_filled:
        save_master_rows(header, master_data)

    count = rebuild_catalog()
    print(f'\nDone: {probed} preview durations written, {failed} failed.')
    print(f'Rebuilt videos/catalog.json ({count} clips).')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
