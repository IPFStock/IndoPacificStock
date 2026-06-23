#!/usr/bin/env python3
"""Merge DaVinci export CSVs from imports/ into the master metadata CSV."""

from __future__ import annotations

import csv
import json
import re
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / 'Raja Stock Clips 3 Clips Metadata.csv'
BACKUP = ROOT / 'Raja Stock Clips 3 Clips Metadata.backup.csv'
IMPORTS_DIR = ROOT / 'imports'
GITHUB_API = 'https://api.github.com/repos/IPFStock/ip-assets-01/contents/?ref=main'


def read_csv(path: Path) -> list[list[str]]:
    raw = path.read_bytes()
    if raw[:2] == b'\xff\xfe':
        text = raw.decode('utf-16le').lstrip('\ufeff')
    elif raw[:3] == b'\xef\xbb\xbf':
        text = raw.decode('utf-8-sig')
    else:
        text = raw.decode('utf-8', errors='replace')
    lines = text.splitlines()
    if not lines:
        return []
    delimiter = '\t' if lines[0].count('\t') > lines[0].count(',') else ','
    return list(csv.reader(lines, delimiter=delimiter))


def write_csv(path: Path, rows: list[list[str]]) -> None:
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)


def reel_base(name: str) -> str:
    base = re.sub(r'\.(r3d|mp4|mov)$', '', name, flags=re.I)
    base = re.sub(r'_V\d+-\d+$', '', base, flags=re.I)
    base = re.sub(r'_\d{3}$', '', base)
    return base.upper()


def slugify_title(title: str) -> str:
    value = re.sub(r'[^\w\s-]', '', title.lower())
    value = re.sub(r'[\s_]+', '-', value).strip('-')
    return value or 'archive'


def parse_location(description: str) -> str:
    text = description.lower()
    if 'cenderawasih' in text or 'cendrawasih' in text:
        return 'Cenderawasih'
    if 'komodo' in text:
        return 'Komodo'
    if 'raja ampat' in text:
        return 'Raja Ampat'
    if 'lembeh' in text:
        return 'Lembeh Strait'
    if 'sumbawa' in text:
        return 'Sumbawa'
    if 'papua' in text:
        return 'Papua'
    return 'Cenderawasih'


def parse_fps(raw: str) -> float:
    try:
        value = float(str(raw).strip())
        return value if value > 0 else 24.0
    except ValueError:
        return 24.0


def parse_timecode_frames(tc: str, fps: float) -> int | None:
    match = re.match(r'^(\d+):(\d{1,2}):(\d{1,2}):(\d{1,3})$', str(tc).strip())
    if not match:
        return None
    hours, minutes, seconds, frames = map(int, match.groups())
    frame_rate = parse_fps(str(fps))
    return round((hours * 3600 + minutes * 60 + seconds) * frame_rate + frames)


def normalize_duration(raw: str, fps: str) -> str:
    value = str(raw or '').strip()
    if not value:
        return ''
    if ' - ' in value:
        start, end = [part.strip() for part in value.split(' - ', 1)]
        start_frames = parse_timecode_frames(start, parse_fps(fps))
        end_frames = parse_timecode_frames(end, parse_fps(fps))
        if start_frames is None or end_frames is None:
            return value
        frame_rate = max(1, round(parse_fps(fps)))
        total = max(0, end_frames - start_frames)
        frames = total % frame_rate
        total_seconds = total // frame_rate
        return (
            f'{total_seconds // 3600:02d}:{(total_seconds % 3600) // 60:02d}:'
            f'{total_seconds % 60:02d}:{frames:02d}'
        )
    return value


def fetch_github_mp4s() -> list[str]:
    request = urllib.request.Request(
        GITHUB_API,
        headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'IndoPacificStock-merge'},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    return sorted(entry['name'] for entry in payload if entry['name'].lower().endswith('.mp4'))


def mp4_variant_index(name: str) -> int:
    match = re.search(r'_V(\d+)-(\d+)$', name, flags=re.I)
    if not match:
        return 0
    return int(match.group(1)) * 10000 + int(match.group(2))


def is_davinci_export(headers: list[str]) -> bool:
    normalized = [h.strip() for h in headers]
    return 'Title' in normalized and 'Description' in normalized and 'File Name' in normalized


def load_export_rows(path: Path) -> list[dict[str, str]]:
    rows = read_csv(path)
    if len(rows) < 2:
        return []

    headers = [h.strip() for h in rows[0]]
    if not is_davinci_export(headers):
        return []

    index = {name: idx for idx, name in enumerate(headers)}
    parsed: list[dict[str, str]] = []

    for row in rows[1:]:
        if len(row) < 4:
            continue
        file_name = row[index['File Name']].strip() if 'File Name' in index else ''
        if not file_name or not re.search(r'\.(r3d|mp4|mov)$', file_name, flags=re.I):
            continue

        title = row[index['Title']].strip() if 'Title' in index else ''
        description = row[index['Description']].strip() if 'Description' in index else ''
        if not title and not description:
            continue

        duration = row[index['Duration TC']].strip() if 'Duration TC' in index else ''
        fps = row[index['Camera FPS']].strip() if 'Camera FPS' in index else '24'
        start_tc = row[index['Start TC']].strip() if 'Start TC' in index else ''
        end_tc = row[index['End TC']].strip() if 'End TC' in index else ''

        # Export5 uses Shot/Scene for pricing tier and license type.
        pricing_tier = row[index['Shot']].strip() if 'Shot' in index else 'Standard'
        license_type = row[index['Scene']].strip() if 'Scene' in index else 'Commercial'
        if pricing_tier.lower() in {'commercial', 'editorial'}:
            pricing_tier, license_type = license_type, pricing_tier

        shoot_category = 'Underwater'
        trailing = [part.strip() for part in row[15:] if part and part.strip()]
        if trailing:
            shoot_category = trailing[-1]

        parsed.append({
            'file_name': file_name,
            'reel_base': reel_base(file_name),
            'duration': normalize_duration(duration, fps),
            'start_tc': start_tc,
            'resolution': row[index['Resolution']].strip() if 'Resolution' in index else '',
            'codec': row[index['Video Codec']].strip() if 'Video Codec' in index else '',
            'title': title,
            'description': description,
            'comments': slugify_title(title),
            'location': parse_location(description),
            'category': shoot_category,
            'camera_type': row[index['Camera Type']].strip() if 'Camera Type' in index else '',
            'camera_format': row[index['Camera Format']].strip() if 'Camera Format' in index else '',
            'fps': fps,
            'aspect_ratio': row[index['Aspect Ratio Notes']].strip() if 'Aspect Ratio Notes' in index else '',
            'license_type': license_type or 'Commercial',
            'pricing_tier': pricing_tier or 'Standard',
        })

    return parsed


def assign_mp4_names(exports: list[dict[str, str]], github_mp4s: list[str]) -> list[dict[str, str]]:
    by_reel: dict[str, list[str]] = {}
    for mp4 in github_mp4s:
        by_reel.setdefault(reel_base(mp4), []).append(mp4)

    for reel, names in by_reel.items():
        names.sort(key=mp4_variant_index)

    assigned: list[dict[str, str]] = []
    grouped: dict[str, list[dict[str, str]]] = {}
    for entry in exports:
        grouped.setdefault(entry['reel_base'], []).append(entry)

    for reel, entries in grouped.items():
        entries.sort(key=lambda item: item.get('start_tc') or item['file_name'])
        candidates = list(by_reel.get(reel, []))
        used: set[str] = set()

        for entry in entries:
            mp4_name = ''
            if len(candidates) == 1:
                mp4_name = candidates[0]
            elif candidates:
                for candidate in candidates:
                    if candidate not in used:
                        mp4_name = candidate
                        break
            if not mp4_name:
                mp4_name = f"{entry['reel_base']}.mp4"
            used.add(mp4_name)
            merged = dict(entry)
            merged['mp4_name'] = mp4_name
            assigned.append(merged)

    return assigned


def build_master_row(entry: dict[str, str], width: int) -> list[str]:
    row = [''] * width
    row[0] = entry['mp4_name']
    row[2] = entry['duration']
    row[5] = entry['resolution']
    row[6] = entry['codec']
    row[7] = entry['description']
    row[8] = entry['comments']
    row[10] = entry['location']
    row[11] = entry['category']
    row[16] = '16'
    row[21] = entry['camera_type']
    row[24] = entry['camera_format']
    row[25] = entry['fps']
    row[35] = entry['aspect_ratio']
    row[36] = entry['license_type']
    row[37] = entry['pricing_tier']
    return row


def main() -> int:
    import_paths = sorted(IMPORTS_DIR.glob('IPF_STOCK_FOOTAGE_export*.csv'))
    if not import_paths:
        print('No IPF_STOCK_FOOTAGE_export*.csv files found in imports/.')
        return 1

    latest_import = import_paths[-1]
    export_rows = load_export_rows(latest_import)
    if not export_rows:
        print(f'No mergeable export rows found in {latest_import.name}.')
        return 1

    github_mp4s = fetch_github_mp4s()
    assigned = assign_mp4_names(export_rows, github_mp4s)

    master_rows = read_csv(MASTER)
    header = master_rows[0]
    width = len(header)
    data = [(row + [''] * width)[:width] for row in master_rows[1:]]
    existing = {row[0].strip().lower() for row in data if row[0].strip()}

    added = 0
    updated = 0
    for entry in assigned:
        mp4_key = entry['mp4_name'].lower()
        new_row = build_master_row(entry, width)
        if mp4_key in existing:
            for row in data:
                if row[0].strip().lower() != mp4_key:
                    continue
                for idx, value in enumerate(new_row):
                    if value and (idx >= len(row) or not row[idx].strip()):
                        row[idx] = value
                updated += 1
                break
            continue
        data.append(new_row)
        existing.add(mp4_key)
        added += 1

    shutil.copy2(MASTER, BACKUP)
    write_csv(MASTER, [header, *data])

    print(f'Import source: {latest_import.name}')
    print(f'Export rows parsed: {len(export_rows)}')
    print(f'Rows added to master: {added}')
    print(f'Rows updated in master: {updated}')
    print(f'Master clip count: {len(data)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
