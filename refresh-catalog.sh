#!/bin/bash
# Refresh Numbers → CSV → site catalog (videos/*.json)
cd "$(dirname "$0")" || exit 1
echo "→ Indo Pacific Stock catalog refresh"
echo "  (Exports Numbers, syncs GitHub MP4s, probes durations via ffprobe)"
echo ""
node ingest.js "$@"
