#!/usr/bin/env python3
"""Move MP4 moov atoms to the file start for faster web playback (stream-friendly previews).

The 720p preview files in IPFStock/ip-assets-01 currently store metadata at the end of
each MP4, which forces browsers to fetch large ranges before playback can begin.
This script remuxes each file with ffmpeg -movflags +faststart (no re-encode).

Typical workflow
----------------
1. Clone the preview asset repo locally:
     git clone https://github.com/IPFStock/ip-assets-01.git
2. Dry-run:
     python3 scripts/faststart_previews.py --input-dir ../ip-assets-01 --dry-run
3. Optimize in place:
     python3 scripts/faststart_previews.py --input-dir ../ip-assets-01 --in-place
4. Commit and push inside ip-assets-01:
     git add *.mp4 && git commit -m "Faststart 720p previews for web streaming" && git push
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIDEOS_DIR = ROOT / 'videos'
MANIFEST = VIDEOS_DIR / 'manifest.json'
FASTSTART_PROBE_BYTES = 1024 * 1024

DEFAULT_INPUT_DIRS = [
    ROOT.parent / 'ip-assets-01',
    Path('/Users/michaelveitch/Desktop/ip-assets-01'),
    Path('/Users/michaelveitch/Desktop/IPFStock/ip-assets-01'),
]


def find_ffmpeg() -> str | None:
    env = os.environ.get('FFMPEG')
    if env and Path(env).exists():
        return env

    for candidate in (
        'ffmpeg',
        '/opt/homebrew/bin/ffmpeg',
        '/usr/local/bin/ffmpeg',
    ):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def catalog_mp4_names() -> list[str]:
    names: set[str] = set()
    if MANIFEST.exists():
        slugs = json.loads(MANIFEST.read_text(encoding='utf-8'))
        for slug in slugs:
            json_path = VIDEOS_DIR / f'{slug}.json'
            if not json_path.exists():
                continue
            data = json.loads(json_path.read_text(encoding='utf-8'))
            file_name = (data.get('technicalSpecs') or {}).get('fileName')
            if file_name:
                names.add(file_name)
    if names:
        return sorted(names)

    for json_path in sorted(VIDEOS_DIR.glob('*.json')):
        if json_path.name == 'manifest.json':
            continue
        data = json.loads(json_path.read_text(encoding='utf-8'))
        file_name = (data.get('technicalSpecs') or {}).get('fileName')
        if file_name:
            names.add(file_name)
    return sorted(names)


def has_faststart(path: Path) -> bool:
    with path.open('rb') as handle:
        head = handle.read(FASTSTART_PROBE_BYTES)
    return b'moov' in head


def remux_faststart(ffmpeg: str, source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        '-hide_banner',
        '-loglevel',
        'error',
        '-y',
        '-i',
        str(source),
        '-c',
        'copy',
        '-movflags',
        '+faststart',
        str(destination),
    ]
    subprocess.run(command, check=True)


def resolve_input_dir(explicit: str | None) -> Path | None:
    if explicit:
        path = Path(explicit).expanduser().resolve()
        return path if path.exists() else None

    for candidate in DEFAULT_INPUT_DIRS:
        if candidate.exists():
            return candidate.resolve()
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--input-dir',
        help='Folder containing preview MP4 files (e.g. cloned ip-assets-01 repo)',
    )
    parser.add_argument(
        '--output-dir',
        help='Write optimized copies here instead of modifying originals',
    )
    parser.add_argument(
        '--in-place',
        action='store_true',
        help='Replace each source MP4 with a faststart version',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Report which files need faststart without running ffmpeg',
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=0,
        help='Only process the first N files that need faststart',
    )
    args = parser.parse_args()

    input_dir = resolve_input_dir(args.input_dir)
    if input_dir is None:
        print('Could not find preview MP4 folder.')
        print('Clone the asset repo, then run:')
        print('  git clone https://github.com/IPFStock/ip-assets-01.git')
        print('  python3 scripts/faststart_previews.py --input-dir ../ip-assets-01 --dry-run')
        return 1

    if args.in_place and args.output_dir:
        print('Use either --in-place or --output-dir, not both.')
        return 1

    ffmpeg = find_ffmpeg()
    if not args.dry_run and not ffmpeg:
        print('ffmpeg not found. Install it first, for example:')
        print('  brew install ffmpeg')
        print('Or set FFMPEG=/path/to/ffmpeg')
        return 1

    expected = catalog_mp4_names()
    mp4_paths = [input_dir / name for name in expected if (input_dir / name).exists()]
    missing = [name for name in expected if not (input_dir / name).exists()]

    if not mp4_paths:
        print(f'No catalog MP4 files found in {input_dir}')
        return 1

    needs_work = [path for path in mp4_paths if not has_faststart(path)]
    already_ok = [path for path in mp4_paths if has_faststart(path)]

    print(f'Input folder: {input_dir}')
    print(f'Catalog MP4s found: {len(mp4_paths)}')
    print(f'Already faststart: {len(already_ok)}')
    print(f'Need faststart: {len(needs_work)}')
    if missing:
        print(f'Missing from folder: {len(missing)}')

    if args.dry_run:
        for path in needs_work[:20]:
            print(f'  would optimize: {path.name}')
        if len(needs_work) > 20:
            print(f'  ... and {len(needs_work) - 20} more')
        return 0

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None
    targets = needs_work[: args.limit] if args.limit > 0 else needs_work
    processed = 0
    errors = 0

    for source in targets:
        try:
            if args.in_place:
                with tempfile.NamedTemporaryFile(
                    suffix='.mp4',
                    dir=source.parent,
                    delete=False,
                ) as tmp:
                    temp_path = Path(tmp.name)
                remux_faststart(ffmpeg, source, temp_path)
                temp_path.replace(source)
            elif output_dir:
                destination = output_dir / source.name
                remux_faststart(ffmpeg, source, destination)
            else:
                destination = source.with_name(f'{source.stem}.faststart{source.suffix}')
                remux_faststart(ffmpeg, source, destination)
                print(f'Wrote {destination.name} (original left unchanged)')

            processed += 1
            print(f'Optimized: {source.name}')
        except subprocess.CalledProcessError as exc:
            errors += 1
            print(f'Failed: {source.name} ({exc})', file=sys.stderr)

    print(f'Done. Optimized {processed} file(s). Errors: {errors}.')
    if args.in_place and processed:
        print('Next: inside ip-assets-01 run git add, commit, and push so the live site picks up faster previews.')
    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
