#!/usr/bin/env python3
"""Merge Duration TC from DaVinci export spreadsheets into the master metadata CSV."""

from __future__ import annotations

import csv
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / 'Raja Stock Clips 3 Clips Metadata.csv'
BACKUP = ROOT / 'Raja Stock Clips 3 Clips Metadata.backup.csv'

IMPORTS_DIR = ROOT / 'imports'

DEFAULT_SOURCES = [
    IMPORTS_DIR / 'IPF_STOCK_FOOTAGE 22 Clips Media Metadata.csv',
    ROOT / 'IPF_STOCK_FOOTAGE 22 Clips Media Metadata.csv',
    Path('/Users/michaelveitch/Desktop/IPFStock Clips/IPF_STOCK_FOOTAGE 22 Clips Media Metadata.csv'),
]


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
    first = lines[0]
    delimiter = '\t' if first.count('\t') > first.count(',') else ','
    return list(csv.reader(lines, delimiter=delimiter))


def discover_import_sources() -> list[Path]:
    if not IMPORTS_DIR.exists():
        return []
    return sorted(IMPORTS_DIR.glob('*.csv'))


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


def format_duration_from_frames(total_frames: int, fps: float) -> str:
    frame_rate = max(1, round(parse_fps(str(fps))))
    frame_count = max(0, round(total_frames))
    frame_mod = frame_rate
    frames = frame_count % frame_mod
    total_seconds_int = frame_count // frame_rate
    return f'{total_seconds_int // 3600:02d}:{(total_seconds_int % 3600) // 60:02d}:{total_seconds_int % 60:02d}:{frames:02d}'


def normalize_duration_value(raw: str, fps: str) -> str:
    value = str(raw or '').strip()
    if not value:
        return ''
    if ' - ' in value:
        start, end = [part.strip() for part in value.split(' - ', 1)]
        start_frames = parse_timecode_frames(start, parse_fps(fps))
        end_frames = parse_timecode_frames(end, parse_fps(fps))
        if start_frames is None or end_frames is None:
            return value
        return format_duration_from_frames(max(0, end_frames - start_frames), parse_fps(fps))
    return value


def reel_base(name: str) -> str:
    base = re.sub(r'\.(r3d|mp4|mov)$', '', name, flags=re.I)
    base = re.sub(r'_V\d+-\d+$', '', base, flags=re.I)
    base = re.sub(r'_\d{3}$', '', base)
    return base.upper()


def to_r3d_name(name: str) -> str:
    if name.lower().endswith('.r3d'):
        return name
    return f'{reel_base(name)}_001.R3D'


def duration_from_row(row: list[str], headers: dict[str, int]) -> tuple[str, str, str, str]:
    file_name = row[headers['File Name']].strip() if 'File Name' in headers else ''
    duration = row[headers['Duration TC']].strip() if 'Duration TC' in headers else ''
    start = row[headers['Start TC']].strip() if 'Start TC' in headers else ''
    end = row[headers['End TC']].strip() if 'End TC' in headers else ''
    fps = row[headers['Camera FPS']].strip() if 'Camera FPS' in headers else '24'
    if not duration and start and end:
        duration = normalize_duration_value(f'{start} - {end}', fps)
    return file_name, duration, start, end, fps


def load_duration_sources(paths: list[Path]) -> dict[str, dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for path in paths:
        if not path.exists():
            continue
        rows = read_csv(path)
        if not rows:
            continue
        headers = {name.strip(): idx for idx, name in enumerate(rows[0])}
        if 'File Name' not in headers:
            continue
        has_duration = 'Duration TC' in headers
        has_range = 'Start TC' in headers and 'End TC' in headers
        if not has_duration and not has_range:
            continue
        for row in rows[1:]:
            file_name, duration, start, end, fps = duration_from_row(row, headers)
            if not file_name or not duration:
                continue
            merged[file_name.lower()] = {
                'duration': duration,
                'start': start,
                'end': end,
                'fps': fps,
                'source': path.name,
            }
    return merged


def range_matches(master_duration: str, start: str, end: str) -> bool:
    value = master_duration.strip()
    if not value or ' - ' not in value:
        return False
    master_start, master_end = [part.strip() for part in value.split(' - ', 1)]
    return master_start == start and master_end == end


def main() -> int:
    source_paths = []
    for candidate in (
        DEFAULT_SOURCES
        + discover_import_sources()
        + [Path(arg) for arg in sys.argv[1:]]
    ):
        if candidate.exists() and candidate not in source_paths:
            source_paths.append(candidate)

    if not source_paths:
        print('No duration export files found.')
        print('Drop your Excel export as CSV in IndoPacificStock/imports/, then run:')
        print('  python3 scripts/merge_duration_exports.py')
        return 1

    durations = load_duration_sources(source_paths)
    if not durations:
        print('No Duration TC rows found in source files.')
        return 1

    rows = read_csv(MASTER)
    header = rows[0]
    width = len(header)
    data = [(row + [''] * width)[:width] for row in rows[1:]]
    idx = {name.strip(): i for i, name in enumerate(header)}

    updated = 0
    normalized = 0
    for row in data:
        file_name = row[idx['File Name']].strip()
        if not file_name:
            continue

        current = row[idx['Duration TC']].strip()
        fps = row[idx['Camera FPS']].strip() if 'Camera FPS' in idx else '24'
        source = durations.get(file_name.lower())
        if source is None and file_name.lower().endswith('.mp4'):
            source = durations.get(to_r3d_name(file_name).lower())

        if source:
            start = source['start']
            end = source['end']
            next_duration = source['duration']
            if start and end and (not current or range_matches(current, start, end)):
                next_duration = normalize_duration_value(f'{start} - {end}', source['fps'] or fps)
            elif file_name.lower().endswith('.mp4') and current and ' - ' not in current:
                # Keep MP4-specific durations unless the row is still empty or a range.
                next_duration = current
            if next_duration and next_duration != current:
                row[idx['Duration TC']] = next_duration
                updated += 1
                continue

        if current and ' - ' in current:
            normalized_value = normalize_duration_value(current, fps)
            if normalized_value != current:
                row[idx['Duration TC']] = normalized_value
                normalized += 1

    shutil.copy2(MASTER, BACKUP)
    with MASTER.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(data)

    print(f'Sources merged: {", ".join(path.name for path in source_paths)}')
    print(f'Duration rows available in sources: {len(durations)}')
    print(f'Updated from source: {updated}')
    print(f'Normalized existing ranges: {normalized}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
