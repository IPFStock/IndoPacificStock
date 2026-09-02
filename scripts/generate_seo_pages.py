#!/usr/bin/env python3
"""Generate crawlable clip pages, keyword landings, and sitemap.xml from catalog.json."""

from __future__ import annotations

import html
import json
import re
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "videos" / "catalog.json"
CLIP_DIR = ROOT / "clip"
COLLECTIONS_DIR = ROOT / "collections"
SITEMAP_PATH = ROOT / "sitemap.xml"
SITE = "https://indopacificstock.com"
SITE_NAME = "Indo Pacific Stock"
LOGO_URL = f"{SITE}/images/logo.png"
THUMBS_DIR = ROOT / "thumbs"
VIDEO_SITEMAP_PATH = ROOT / "video-sitemap.xml"

ICON_LINKS = """  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
  <link rel="icon" href="/favicon.ico" sizes="any" />
  <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
"""

ORGANIZATION_LD = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "@id": f"{SITE}/#organization",
    "name": SITE_NAME,
    "url": SITE,
    "logo": {
        "@type": "ImageObject",
        "url": LOGO_URL,
        "width": 512,
        "height": 512,
    },
    "email": "licensingips@gmail.com",
}


def organization_publisher() -> dict:
    return {
        "@type": "Organization",
        "@id": f"{SITE}/#organization",
        "name": SITE_NAME,
        "url": SITE,
        "logo": {"@type": "ImageObject", "url": LOGO_URL, "width": 512, "height": 512},
    }

SHARED_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #F8FAFC; --surface: #FFFFFF; --border: #E6E8EA; --text: #0F172A;
  --text-secondary: #334155; --muted: #64748b; --accent: #1D6FA8;
  --header-bg: rgba(255, 255, 255, 0.96); --header-h: 4rem;
  --layout-max: 75rem; --layout-gutter: 1.5rem;
  --font: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --radius-sm: 8px; --radius-md: 12px; --transition: 200ms ease;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
}
html { scroll-behavior: smooth; }
body {
  font-family: var(--font); background: var(--bg); color: var(--text);
  line-height: 1.55; min-height: 100vh; display: flex; flex-direction: column;
  -webkit-font-smoothing: antialiased;
}
.layout-rail {
  width: 100%; max-width: var(--layout-max); margin-left: auto; margin-right: auto;
  padding-left: var(--layout-gutter); padding-right: var(--layout-gutter);
}
.site-header {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100; height: var(--header-h);
  background: var(--header-bg); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border); box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.site-header-rail { height: 100%; display: flex; align-items: center; justify-content: space-between; }
.logo { display: flex; align-items: center; gap: 1rem; text-decoration: none; color: inherit; }
.logo:hover { opacity: 0.88; }
.logo-icon { width: 1.5rem; height: 1.5rem; display: block; flex-shrink: 0; }
.logo-wordmark {
  font-size: 1.25rem; font-weight: 500; line-height: 1; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--text); white-space: nowrap;
}
.header-nav { display: flex; align-items: center; gap: 1.35rem; }
.inquire-link {
  font-size: 0.82rem; font-weight: 400; color: var(--text-secondary);
  text-decoration: none; transition: color 0.2s ease;
}
.inquire-link:hover, .inquire-link.is-current { color: var(--accent); }
main { flex: 1; padding-top: calc(var(--header-h) + 2.25rem); padding-bottom: 3.5rem; }
.kicker {
  margin: 0 0 0.5rem; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--accent);
}
.page-title {
  margin: 0; font-size: clamp(1.45rem, 3vw, 2rem); font-weight: 700; line-height: 1.25;
}
.page-lead { margin: 0.85rem 0 0; font-size: 1rem; color: var(--text-secondary); max-width: 46rem; }
.page-meta { margin: 0.75rem 0 0; font-size: 0.85rem; color: var(--muted); }
.badge {
  display: inline-block; margin-top: 0.85rem; padding: 0.2rem 0.55rem; border-radius: 999px;
  border: 1px solid rgba(29, 111, 168, 0.35); background: rgba(29, 111, 168, 0.08);
  color: var(--accent); font-size: 0.72rem; font-weight: 600; letter-spacing: 0.04em;
}
.clip-layout {
  display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: 2rem; margin-top: 1.75rem;
}
.video-panel {
  background: #0F172A; border-radius: var(--radius-md); overflow: hidden; aspect-ratio: 16 / 9;
}
.video-panel video { width: 100%; height: 100%; display: block; object-fit: contain; background: #0F172A; }
.detail-panel { display: grid; gap: 1rem; align-content: start; }
.detail-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm);
  padding: 1.15rem 1.25rem;
}
.detail-card h2 {
  margin: 0 0 0.75rem; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--muted);
}
.detail-card p, .detail-card li { font-size: 0.9rem; color: var(--text-secondary); line-height: 1.65; }
.detail-card ul { margin: 0; padding-left: 1.1rem; display: grid; gap: 0.35rem; }
.spec-grid {
  display: grid; grid-template-columns: auto 1fr; gap: 0.45rem 1rem; font-size: 0.88rem;
}
.spec-grid dt { color: var(--muted); }
.spec-grid dd { color: var(--text); margin: 0; }
.cta-row { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 0.25rem; }
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 0.4rem;
  padding: 0.7rem 1.1rem; border-radius: var(--radius-sm); font-size: 0.88rem; font-weight: 600;
  text-decoration: none; transition: background var(--transition), color var(--transition), border-color var(--transition);
}
.btn-primary { background: var(--accent); color: #fff; border: 1px solid var(--accent); }
.btn-primary:hover { background: #185B8A; border-color: #185B8A; }
.btn-secondary {
  background: var(--surface); color: var(--text); border: 1px solid var(--border);
}
.btn-secondary:hover { border-color: var(--accent); color: var(--accent); }
.clip-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1rem; margin-top: 1.75rem;
}
.clip-card {
  display: flex; flex-direction: column; background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-sm); overflow: hidden; text-decoration: none; color: inherit;
  box-shadow: var(--shadow-sm); transition: border-color var(--transition), transform var(--transition);
}
.clip-card:hover { border-color: rgba(29, 111, 168, 0.45); transform: translateY(-1px); }
.clip-card-media { background: #0F172A; aspect-ratio: 16 / 9; }
.clip-card-media video { width: 100%; height: 100%; object-fit: cover; display: block; }
.clip-card-body { padding: 0.9rem 1rem 1.1rem; display: grid; gap: 0.35rem; }
.clip-card-title { font-size: 0.92rem; font-weight: 600; line-height: 1.35; color: var(--text); }
.clip-card-meta { font-size: 0.75rem; color: var(--muted); }
.clip-card-desc {
  font-size: 0.8rem; color: var(--text-secondary); line-height: 1.45;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}
.prose { max-width: 46rem; margin-top: 1.25rem; display: grid; gap: 0.9rem; }
.prose p, .prose li { font-size: 0.95rem; color: var(--text-secondary); line-height: 1.7; }
.prose ul { padding-left: 1.15rem; display: grid; gap: 0.45rem; }
.prose strong { color: var(--text); font-weight: 600; }
.related { margin-top: 2.5rem; }
.related h2 { font-size: 1.15rem; margin-bottom: 0.25rem; }
.breadcrumbs {
  display: flex; flex-wrap: wrap; gap: 0.35rem; align-items: center;
  font-size: 0.78rem; color: var(--muted); margin-bottom: 1.25rem;
}
.breadcrumbs a { color: var(--muted); text-decoration: none; }
.breadcrumbs a:hover { color: var(--accent); }
.collection-list {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1rem; margin-top: 1.75rem;
}
.collection-card {
  display: block; padding: 1.2rem 1.25rem; background: var(--surface);
  border: 1px solid var(--border); border-radius: var(--radius-sm); text-decoration: none; color: inherit;
}
.collection-card:hover { border-color: rgba(29, 111, 168, 0.45); }
.collection-card h2 { font-size: 1.05rem; margin: 0 0 0.45rem; }
.collection-card p { font-size: 0.85rem; color: var(--text-secondary); margin: 0; line-height: 1.5; }
.site-footer {
  padding: 0.85rem 1.25rem; background: rgba(255, 255, 255, 0.94);
  border-top: 1px solid var(--border); text-align: center;
}
.site-footer-line { margin: 0; font-size: 0.82rem; color: var(--muted); line-height: 1.45; }
.site-footer-line a { color: inherit; text-decoration: none; }
.site-footer-line a:hover { text-decoration: underline; }
@media (max-width: 900px) {
  .clip-layout { grid-template-columns: 1fr; gap: 1.25rem; }
}
@media (max-width: 768px) {
  .logo-wordmark { font-size: 0.82rem; letter-spacing: 0.06em; }
  .header-nav { gap: 0.85rem; }
  .inquire-link { font-size: 0.75rem; }
  main { padding-top: calc(var(--header-h) + 1.5rem); }
}
"""

LOGO_SVG = """
<svg class="logo-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <path fill="#1D6FA8" d="M14.533 9.034L12.816 1.632A10.40 10.40 0 0 1 21.608 8.020L15.792 12.910Z"/>
  <path fill="#1D6FA8" d="M15.603 13.492L22.113 9.572A10.40 10.40 0 0 1 18.754 19.908L12.306 15.888Z"/>
  <path fill="#1D6FA8" d="M11.694 15.888L17.434 20.867A10.40 10.40 0 0 1 6.566 20.867L8.397 13.492Z"/>
  <path fill="#1D6FA8" d="M8.208 12.910L5.246 19.908A10.40 10.40 0 0 1 1.887 9.572L9.467 9.034Z"/>
  <path fill="#1D6FA8" d="M9.962 8.675L2.392 8.020A10.40 10.40 0 0 1 11.184 1.632L14.038 8.675Z"/>
  <circle cx="12" cy="12" r="10.40" stroke="#1D6FA8" stroke-width="0.9"/>
</svg>
"""


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def text_blob(clip: dict) -> str:
    parts = [
        clip.get("title"),
        clip.get("description"),
        clip.get("category"),
        clip.get("region"),
        clip.get("species"),
        clip.get("behavior"),
        clip.get("format"),
        clip.get("camera"),
        clip.get("nativeFormatBadge"),
        " ".join(clip.get("keywords") or []),
        " ".join(clip.get("availableSizes") or []),
        (clip.get("technicalSpecs") or {}).get("family"),
        (clip.get("technicalSpecs") or {}).get("latinName"),
        (clip.get("technicalSpecs") or {}).get("resolution"),
    ]
    return " ".join(str(p) for p in parts if p).lower()


def camera_id_slug(clip: dict) -> str:
    """Old clip URL used the camera filename only, e.g. a006-a009-0413qe-v1-0003."""
    specs = clip.get("technicalSpecs") or {}
    code = specs.get("originalCameraCode") or ""
    if not code:
        return ""
    return Path(code).stem.lower().replace("_", "-")


def clip_code(clip: dict) -> str:
    specs = clip.get("technicalSpecs") or {}
    raw = (
        specs.get("originalCameraCode")
        or specs.get("fileName")
        or ""
    )
    return Path(raw).stem if raw else ""


def clip_title(clip: dict) -> str:
    return (clip.get("title") or clip.get("slug") or "").strip()


def take_label_map(clips: list[dict]) -> dict[str, str]:
    """When several clips share a title, label them Take 1 of N, Take 2 of N, …"""
    groups: dict[str, list[dict]] = defaultdict(list)
    for clip in clips:
        title = clip_title(clip)
        if title:
            groups[title].append(clip)
    labels: dict[str, str] = {}
    for group in groups.values():
        if len(group) < 2:
            continue
        ordered = sorted(group, key=lambda c: (clip_code(c) or c.get("slug") or "").lower())
        total = len(ordered)
        for index, clip in enumerate(ordered, 1):
            slug = clip.get("slug")
            if slug:
                labels[slug] = f"Take {index} of {total}"
    return labels


def display_title(clip: dict, take_labels: dict[str, str]) -> str:
    title = clip_title(clip)
    label = take_labels.get(clip.get("slug") or "")
    return f"{title} — {label}" if label else title


def clip_url(slug: str) -> str:
    return f"{SITE}/clip/{slug}/"


def collection_url(slug: str) -> str:
    return f"{SITE}/collections/{slug}/"


def thumb_path(slug: str) -> Path:
    return THUMBS_DIR / f"{slug}.jpg"


def thumb_url(slug: str) -> str:
    path = thumb_path(slug)
    if path.exists() and path.stat().st_size > 2000:
        return f"{SITE}/thumbs/{quote(slug)}.jpg"
    return ""


def parse_fps(raw: object) -> float:
    value = str(raw or "").strip()
    if not value:
        return 24.0
    if "/" in value:
        num, den = value.split("/", 1)
        try:
            fps = float(num) / float(den)
            return fps if fps > 0 else 24.0
        except ValueError:
            return 24.0
    try:
        fps = float(value)
        return fps if fps > 0 else 24.0
    except ValueError:
        return 24.0


def clip_duration_seconds(
    duration: object, fps: object = None, duration_seconds: object = None
) -> float | None:
    try:
        if duration_seconds not in (None, ""):
            parsed = float(duration_seconds)
            if parsed > 0:
                return parsed
    except (TypeError, ValueError):
        pass

    raw = str(duration or "").strip()
    if not raw:
        return None

    iso = re.match(
        r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?$", raw, re.I
    )
    if iso and any(iso.group(i) for i in range(1, 4)):
        hours = int(iso.group(1) or 0)
        minutes = int(iso.group(2) or 0)
        seconds = float(iso.group(3) or 0)
        total = hours * 3600 + minutes * 60 + seconds
        return total if total > 0 else None

    match = re.match(r"^(\d+):(\d{1,2}):(\d{1,2})(?::(\d{1,3}))?$", raw)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        frames = int(match.group(4) or 0)
        frame_rate = parse_fps(fps)
        total = hours * 3600 + minutes * 60 + seconds + (
            frames / frame_rate if frames else 0
        )
        return total if total > 0 else None

    try:
        parsed = float(raw)
        return parsed if parsed > 0 else None
    except ValueError:
        return None


def iso8601_duration(duration: object, fps: object = None, duration_seconds: object = None) -> str:
    """Convert catalog clip length to schema.org / Google ISO 8601 duration (PT#H#M#S)."""
    total = clip_duration_seconds(duration, fps, duration_seconds)
    if total is None or total <= 0:
        return ""

    whole = int(round(total))
    if whole <= 0:
        return ""

    hours, remainder = divmod(whole, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = ["PT"]
    if hours:
        parts.append(f"{hours}H")
    if minutes:
        parts.append(f"{minutes}M")
    if seconds or len(parts) == 1:
        parts.append(f"{seconds}S")
    return "".join(parts)


def format_duration_label(
    duration: object, fps: object = None, duration_seconds: object = None
) -> str:
    total = clip_duration_seconds(duration, fps, duration_seconds)
    if total is None or total <= 0:
        return str(duration or "").strip()
    whole = max(0, int(round(total)))
    hours, remainder = divmod(whole, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def header_html(active: str | None = None) -> str:
    def nav(href: str, label: str, key: str) -> str:
        cls = "inquire-link is-current" if active == key else "inquire-link"
        current = ' aria-current="page"' if active == key else ""
        return f'<a href="{href}" class="{cls}"{current}>{label}</a>'

    return f"""
  <header class="site-header">
    <div class="layout-rail site-header-rail">
      <a href="/" class="logo" aria-label="Indo Pacific Stock home">
        {LOGO_SVG}
        <span class="logo-wordmark">Indo Pacific Stock</span>
      </a>
      <nav class="header-nav" aria-label="Site navigation">
        {nav('/collections/', 'Collections', 'collections')}
        {nav('/licensing-guide.html', 'How it Works', 'guide')}
        {nav('/inquire.html', 'Inquire', 'inquire')}
      </nav>
    </div>
  </header>
"""


def footer_html() -> str:
    year = datetime.now(timezone.utc).year
    return f"""
  <footer class="site-footer">
    <p class="site-footer-line">© {year} Indo Pacific Stock · All footage rights reserved · <a href="/collections/">Collections</a> · <a href="/terms.html">Terms</a> · <a href="/license-terms.html">License Terms</a> · <a href="/privacy.html">Privacy</a></p>
  </footer>
"""


def page_shell(
    *,
    title: str,
    description: str,
    canonical: str,
    body: str,
    json_ld: dict | list | None = None,
    og_type: str = "website",
    og_image: str | None = None,
    active_nav: str | None = None,
    keywords: str | None = None,
) -> str:
    keywords_tag = (
        f'  <meta name="keywords" content="{esc(keywords)}" />\n' if keywords else ""
    )
    image = og_image or LOGO_URL
    twitter_card = "summary_large_image" if og_image else "summary"
    ld_blocks = [
        '  <script type="application/ld+json">\n'
        f"  {json.dumps(ORGANIZATION_LD, ensure_ascii=False)}\n"
        "  </script>\n"
    ]
    if json_ld is not None:
        ld_blocks.append(
            '  <script type="application/ld+json">\n'
            f"  {json.dumps(json_ld, ensure_ascii=False)}\n"
            "  </script>\n"
        )
    ld = "".join(ld_blocks)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}" />
{keywords_tag}  <link rel="canonical" href="{esc(canonical)}" />
{ICON_LINKS}  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:type" content="{esc(og_type)}" />
  <meta property="og:url" content="{esc(canonical)}" />
  <meta property="og:site_name" content="{esc(SITE_NAME)}" />
  <meta property="og:image" content="{esc(image)}" />
  <meta name="twitter:card" content="{twitter_card}" />
  <meta name="twitter:title" content="{esc(title)}" />
  <meta name="twitter:description" content="{esc(description)}" />
  <meta name="twitter:image" content="{esc(image)}" />
{ld}  <style>{SHARED_CSS}</style>
</head>
<body>
{header_html(active_nav)}
{body}
{footer_html()}
</body>
</html>
"""


def clip_card_html(clip: dict, take_labels: dict[str, str] | None = None) -> str:
    slug = clip["slug"]
    title = display_title(clip, take_labels or {})
    desc = clip.get("description") or ""
    meta_bits = [clip.get("region"), clip.get("nativeFormatBadge") or clip.get("format"), "Rights Managed"]
    meta = " · ".join(bit for bit in meta_bits if bit)
    video = clip.get("videoUrl") or ""
    poster = thumb_url(slug)
    poster_attr = f' poster="{esc(poster)}"' if poster else ""
    return f"""
    <a class="clip-card" href="/clip/{esc(slug)}/">
      <div class="clip-card-media">
        <video muted preload="metadata" playsinline{poster_attr} src="{esc(video)}"></video>
      </div>
      <div class="clip-card-body">
        <div class="clip-card-title">{esc(title)}</div>
        <div class="clip-card-meta">{esc(meta)}</div>
        <p class="clip-card-desc">{esc(desc)}</p>
      </div>
    </a>
"""


def related_clips(clip: dict, catalog: list[dict], limit: int = 6) -> list[dict]:
    slug = clip["slug"]
    region = (clip.get("region") or "").lower()
    category = (clip.get("category") or "").lower()
    species = (clip.get("species") or "").lower()
    scored: list[tuple[int, dict]] = []
    for other in catalog:
        if other["slug"] == slug:
            continue
        score = 0
        if region and (other.get("region") or "").lower() == region:
            score += 3
        if category and (other.get("category") or "").lower() == category:
            score += 2
        if species and species in (other.get("species") or "").lower():
            score += 4
        if clip_title(other) and clip_title(other) == clip_title(clip):
            score += 8
        if score:
            scored.append((score, other))
    scored.sort(key=lambda item: (-item[0], item[1].get("title") or ""))
    picks = [item[1] for item in scored[:limit]]
    if len(picks) < limit:
        for other in catalog:
            if other["slug"] == slug or other in picks:
                continue
            picks.append(other)
            if len(picks) >= limit:
                break
    return picks


def master_delivery_label(clip: dict) -> str:
    """Human-facing master options — R3D at native res, not assumed 8K."""
    specs = clip.get("technicalSpecs") or {}
    resolution = (specs.get("resolution") or "").strip()
    badge = (clip.get("nativeFormatBadge") or clip.get("format") or "").strip()
    native = ""
    if resolution:
        native = f"R3D at native resolution ({resolution})"
    elif badge and re.search(r"\b([45678]K)\b", badge, re.I):
        native = f"R3D at native {re.search(r'[45678]K', badge, re.I).group(0)} resolution"
    else:
        native = "R3D at native camera resolution (4K–8K depending on the clip)"
    return f"{native}; 4K ProRes 422 HQ; 1080p Master"


def build_clip_page(clip: dict, catalog: list[dict], take_labels: dict[str, str] | None = None) -> str:
    take_labels = take_labels or {}
    slug = clip["slug"]
    base_title = clip.get("title") or slug
    title = display_title(clip, take_labels)
    take = take_labels.get(slug) or ""
    code = clip_code(clip)
    description = clip.get("description") or (
        f"{base_title} — rights-managed Indo-Pacific stock footage available to license as R3D."
    )
    original_description = description
    if take:
        unique_line = f"{take}." + (f" Clip ID {code}." if code else "")
        description = f"{original_description.rstrip('. ')}. {unique_line}".strip()
        meta_source = f"{unique_line} {original_description}".strip()
    else:
        meta_source = original_description
    page_title = f"{title} | License R3D Stock Footage | {SITE_NAME}"
    meta_desc = meta_source[:155] + ("…" if len(meta_source) > 155 else "")
    specs = clip.get("technicalSpecs") or {}
    keywords = clip.get("keywords") or []
    keyword_str = ", ".join(keywords[:24])
    inquire_params = [f"clip={quote(slug, safe='')}"]
    if title:
        inquire_params.append(f"title={quote(title, safe='')}")
    if code:
        inquire_params.append(f"id={quote(code, safe='')}")
    inquire = f"/inquire.html?{'&'.join(inquire_params)}"
    duration = format_duration_label(
        specs.get("duration"), specs.get("fps"), specs.get("durationSeconds")
    )
    schema_duration = iso8601_duration(
        specs.get("duration"), specs.get("fps"), specs.get("durationSeconds")
    )
    upload = specs.get("date") or "2026-03-01"
    if not re.match(r"^\d{4}-\d{2}-\d{2}", str(upload)):
        upload = "2026-03-01"
    masters = master_delivery_label(clip)
    still = thumb_url(slug)
    json_ld = {
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": title,
        "description": description,
        "contentUrl": clip.get("videoUrl"),
        "uploadDate": f"{str(upload)[:10]}T00:00:00Z",
        "keywords": keywords[:30],
        "author": {"@type": "Organization", "name": SITE_NAME},
        "publisher": organization_publisher(),
        "isFamilyFriendly": True,
        "license": f"{SITE}/license-terms.html",
        "encodingFormat": "video/r3d",
    }
    if code:
        json_ld["identifier"] = code
    if still:
        json_ld["thumbnailUrl"] = still
    if schema_duration:
        json_ld["duration"] = schema_duration
    specs_rows = []
    for label, value in [
        ("Region", clip.get("region")),
        ("Category", clip.get("category")),
        ("Species", clip.get("species")),
        ("Family", specs.get("family")),
        ("Latin name", specs.get("latinName")),
        ("Camera", clip.get("camera")),
        ("Format", clip.get("format") or clip.get("nativeFormatBadge")),
        ("Resolution", specs.get("resolution")),
        ("Codec", specs.get("codec") or "r3d"),
        ("Duration", duration),
        ("Clip ID", code),
        ("License", "Rights Managed (RM)"),
        ("Available masters", masters),
    ]:
        if value:
            specs_rows.append(f"<dt>{esc(label)}</dt><dd>{esc(value)}</dd>")

    related = related_clips(clip, catalog)
    related_html = "".join(clip_card_html(item, take_labels) for item in related)
    poster_attr = f' poster="{esc(still)}"' if still else ""

    body = f"""
  <main>
    <div class="layout-rail">
      <nav class="breadcrumbs" aria-label="Breadcrumb">
        <a href="/">Home</a><span>/</span>
        <a href="/collections/">Collections</a><span>/</span>
        <span>{esc(title)}</span>
      </nav>
      <p class="kicker">Rights-managed stock clip</p>
      <h1 class="page-title">{esc(title)}</h1>
      <p class="page-lead">{esc(description)}</p>
      <span class="badge">License R3D · Rights Managed</span>

      <div class="clip-layout">
        <div class="video-panel">
          <video controls playsinline preload="metadata"{poster_attr} src="{esc(clip.get('videoUrl'))}"
            aria-label="{esc(title)} preview"></video>
        </div>
        <aside class="detail-panel">
          <div class="detail-card">
            <h2>License this clip</h2>
            <p>Request a rights-managed license and master delivery as R3D at the clip’s native resolution (4K, 5K, 6K, or 8K depending on the original capture), plus 4K ProRes 422 HQ or 1080p. Ideal for documentary, broadcast, and commercial natural-history projects.</p>
            <div class="cta-row">
              <a class="btn btn-primary" href="{inquire}">Request license</a>
              <a class="btn btn-secondary" href="/licensing-guide.html">How licensing works</a>
            </div>
          </div>
          <div class="detail-card">
            <h2>Technical details</h2>
            <dl class="spec-grid">
              {''.join(specs_rows)}
            </dl>
          </div>
        </aside>
      </div>

      <section class="related" aria-labelledby="related-heading">
        <h2 id="related-heading">Related stock footage</h2>
        <p class="page-meta">More rights-managed Indo-Pacific clips from the archive.</p>
        <div class="clip-grid">
          {related_html}
        </div>
      </section>
    </div>
  </main>
"""
    return page_shell(
        title=page_title,
        description=meta_desc,
        canonical=clip_url(slug),
        body=body,
        json_ld=json_ld,
        og_type="video.other",
        og_image=still or None,
        keywords=keyword_str or None,
    )


CollectionDef = dict


def collection_defs() -> list[CollectionDef]:
    def match_any(*needles: str) -> Callable[[dict], bool]:
        needles_l = [n.lower() for n in needles]

        def _match(clip: dict) -> bool:
            blob = text_blob(clip)
            return any(n in blob for n in needles_l)

        return _match

    def match_region(*regions: str) -> Callable[[dict], bool]:
        regions_l = [r.lower() for r in regions]

        def _match(clip: dict) -> bool:
            return (clip.get("region") or "").lower() in regions_l

        return _match

    def match_category(*parts: str) -> Callable[[dict], bool]:
        parts_l = [p.lower() for p in parts]

        def _match(clip: dict) -> bool:
            cat = (clip.get("category") or "").lower()
            return any(p in cat for p in parts_l)

        return _match

    return [
        {
            "slug": "license-r3d-footage",
            "title": "License R3D Footage",
            "h1": "License R3D Footage from the Indo-Pacific",
            "description": (
                "License cinematic R3D stock footage from Indo Pacific Stock — "
                "rights-managed underwater and aerial masters at native camera resolution for documentary and commercial use."
            ),
            "keywords": "license R3D footage, REDCODE RAW stock, rights managed R3D video, RED Digital stock footage",
            "match": lambda c: True,
            "limit": 48,
            "paragraphs": [
                "Indo Pacific Stock is a rights-managed archive of cinema-camera masters captured across the Indo-Pacific. Every clip can be licensed as R3D at its native capture resolution — which may be 4K, 5K, 6K, or 8K depending on the camera and project — alongside 4K ProRes and 1080p masters.",
                "Producers searching for camera-original quality need REDCODE RAW for finishing, VFX, and colour-critical delivery. Our R3D masters are built for that workflow — not compressed stock proxies.",
            ],
            "bullets": [
                "Rights-managed licensing with clear commercial and broadcast terms",
                "Native R3D / REDCODE RAW masters plus ProRes deliverables",
                "Natural-history subjects: reefs, megafauna, schooling fish, cultural scenes, and aerials",
            ],
        },
        {
            "slug": "underwater-stock-footage",
            "title": "Underwater Stock Footage",
            "h1": "Underwater Stock Footage — Rights Managed",
            "description": (
                "Browse rights-managed underwater stock footage from Raja Ampat, Komodo, and Cenderawasih — "
                "license cinematic reef and marine wildlife clips as R3D."
            ),
            "keywords": "underwater stock footage, underwater cinema, license underwater video, marine stock footage",
            "match": lambda c: (c.get("category") or "") != "Coastal Landscapes Drone Aerials"
            and (c.get("category") or "") != "Indo-Pacific Cultural Documentations & Editorial Scenes",
            "limit": 48,
            "paragraphs": [
                "Our underwater stock footage is filmed on cinema cameras for natural-history and documentary productions that need authentic Indo-Pacific environments.",
                "Search by species, behavior, or location, then request a rights-managed license for the exact timecode you need.",
            ],
            "bullets": [
                "Reef fish, megafauna, benthic life, and open-ocean sequences",
                "Shot across Indonesia’s richest marine regions",
                "Available to license as R3D / ProRes masters",
            ],
        },
        {
            "slug": "raja-ampat-stock-footage",
            "title": "Raja Ampat Stock Footage",
            "h1": "Raja Ampat Stock Footage",
            "description": (
                "License Raja Ampat stock footage — rights-managed underwater cinema from West Papua’s "
                "coral triangle, available as R3D."
            ),
            "keywords": "Raja Ampat stock footage, Raja Ampat underwater video, West Papua film footage",
            "match": match_region("Raja Ampat"),
            "limit": 48,
            "paragraphs": [
                "Raja Ampat is one of the most biodiverse marine regions on Earth. This collection gathers rights-managed clips captured on location for productions that need authentic West Papua imagery.",
            ],
            "bullets": [
                "Coral reefs, schooling fish, and regional wildlife",
                "Cinema-camera capture suitable for broadcast finishing",
                "Commercial and documentary licensing available",
            ],
        },
        {
            "slug": "cenderawasih-stock-footage",
            "title": "Cenderawasih Bay Stock Footage",
            "h1": "Cenderawasih Bay Stock Footage",
            "description": (
                "License Cenderawasih Bay stock footage — rights-managed whale shark, reef, and "
                "Papuan cultural cinema from Central Papua, available as R3D."
            ),
            "keywords": (
                "Cenderawasih Bay stock footage, Cendrawasih Bay video, Teluk Cenderawasih footage, "
                "Nabire stock footage, whale shark Papua footage"
            ),
            "match": match_region("Cenderawasih"),
            "limit": 48,
            "paragraphs": [
                "Cenderawasih Bay (also spelled Cendrawasih) is the largest location set in this archive: whale sharks at traditional bagan fishing platforms, reef and seagrass sequences, and editorial cultural scenes from Nabire and Central Papua.",
                "Productions that need location-accurate Bird’s Head / Cenderawasih imagery can license these clips as R3D at native resolution, plus 4K ProRes or 1080p masters.",
            ],
            "bullets": [
                "Whale sharks, bagans, and Cenderawasih marine life",
                "Papuan cultural and market scenes (many editorial / no model release)",
                "Rights-managed licensing with cinema-camera masters",
            ],
        },
        {
            "slug": "whale-shark-stock-footage",
            "title": "Whale Shark Stock Footage",
            "h1": "Whale Shark Stock Footage",
            "description": (
                "License whale shark stock footage from Cenderawasih and the Indo-Pacific — "
                "rights-managed cinematic masters available as R3D."
            ),
            "keywords": "whale shark stock footage, whale shark video license, Rhincodon typus footage",
            "match": match_any("whale shark", "whaleshark", "rhincodon"),
            "limit": 48,
            "paragraphs": [
                "Whale shark sequences from our Indo-Pacific archive are rights-managed for documentary and commercial use, with master delivery as R3D at native resolution or ProRes.",
            ],
            "bullets": [
                "Natural swimming and approach behavior",
                "Shot for editorial and natural-history storytelling",
                "Request timecode-based licensing for your cut",
            ],
        },
        {
            "slug": "coral-reef-stock-footage",
            "title": "Coral Reef Stock Footage",
            "h1": "Coral Reef Stock Footage",
            "description": (
                "License coral reef stock footage from the Indo-Pacific — rights-managed reefscapes "
                "and associated marine life available as R3D."
            ),
            "keywords": "coral reef stock footage, reef video license, Indo-Pacific coral footage",
            "match": match_any("coral", "reef"),
            "limit": 48,
            "paragraphs": [
                "Coral reef stock footage from Komodo, Raja Ampat, and Cenderawasih supports climate, conservation, and travel storytelling with cinema-camera fidelity.",
            ],
            "bullets": [
                "Reefscapes, benthic detail, and associated fish life",
                "Rights-managed for broadcast and commercial projects",
                "R3D master options for finishing",
            ],
        },
        {
            "slug": "red-raptor-stock-footage",
            "title": "RED Raptor Stock Footage",
            "h1": "RED Raptor & R3D Stock Footage",
            "description": (
                "License RED Raptor and R3D stock footage from Indo Pacific Stock — "
                "cinema-camera underwater and aerial masters for high-end finishing."
            ),
            "keywords": "RED Raptor stock footage, R3D footage license, REDCODE RAW underwater footage",
            "match": match_any("raptor", "red raw", "r3d", "redcode"),
            "limit": 48,
            "paragraphs": [
                "If your post pipeline expects REDCODE RAW (.R3D), this collection highlights clips available as cinema-camera masters — including RED Raptor-origin material — for colour and VFX-critical work. Native resolution varies by clip (4K–8K).",
            ],
            "bullets": [
                "Camera-original R3D workflows",
                "Paired ProRes and HD masters on request",
                "Rights-managed licensing for professional productions",
            ],
        },
        {
            "slug": "aerial-drone-stock-footage",
            "title": "Aerial Drone Stock Footage",
            "h1": "Aerial & Drone Stock Footage — Indo-Pacific",
            "description": (
                "License aerial and drone stock footage from the Indo-Pacific — coastal landscapes "
                "and cinematic overflights, rights-managed for professional use."
            ),
            "keywords": "aerial stock footage Indo-Pacific, drone stock footage Indonesia, coastal aerial video",
            "match": match_category("coastal", "drone", "aerial"),
            "limit": 48,
            "paragraphs": [
                "Aerial and drone stock footage from our archive covers Indo-Pacific coastlines and landscape context for documentary openers, travel films, and commercial spot work.",
            ],
            "bullets": [
                "Coastal landscapes and establishing shots",
                "Rights-managed aerial licensing",
                "High-resolution masters for finishing",
            ],
        },
        {
            "slug": "rights-managed-wildlife-footage",
            "title": "Rights-Managed Wildlife Footage",
            "h1": "Rights-Managed Wildlife Footage",
            "description": (
                "License rights-managed wildlife footage from the Indo-Pacific — marine megafauna, "
                "predators, and natural-history behavior shot on cinema cameras."
            ),
            "keywords": "rights managed wildlife footage, wildlife stock footage license, natural history video",
            "match": match_category("megafauna", "predator", "elasmobranch", "mammal", "reptile"),
            "limit": 48,
            "paragraphs": [
                "Unlike royalty-free libraries, Indo Pacific Stock licenses wildlife footage under rights-managed terms so usage, territory, and term stay clear for broadcasters and brands.",
            ],
            "bullets": [
                "Marine megafauna and apex predators",
                "Documentary-ready behavior sequences",
                "Commercial and editorial licensing pathways",
            ],
        },
        {
            "slug": "documentary-b-roll-indo-pacific",
            "title": "Documentary B-Roll — Indo-Pacific",
            "h1": "Documentary B-Roll from the Indo-Pacific",
            "description": (
                "License documentary B-roll from the Indo-Pacific — rights-managed natural history, "
                "cultural, and underwater cinema for long-form storytelling."
            ),
            "keywords": "documentary B-roll license, Indo-Pacific documentary footage, natural history B-roll",
            "match": lambda c: True,
            "limit": 36,
            "paragraphs": [
                "Documentary producers use this archive for authentic Indo-Pacific B-roll: underwater wildlife, reef habitats, cultural editorial scenes, and aerial context.",
                "Build a shot list from Reel IDs, request time-coded proxies, then license only the seconds you use.",
            ],
            "bullets": [
                "Built for long-form editorial workflows",
                "Timecode-based rights-managed licensing",
                "R3D and ProRes master delivery",
            ],
        },
        {
            "slug": "komodo-stock-footage",
            "title": "Komodo Stock Footage",
            "h1": "Komodo Stock Footage",
            "description": (
                "License Komodo stock footage — rights-managed underwater and marine cinema from "
                "Komodo National Park and surrounding waters, available as R3D."
            ),
            "keywords": "Komodo stock footage, Komodo underwater video, Komodo National Park film footage",
            "match": match_region("Komodo"),
            "limit": 48,
            "paragraphs": [
                "Komodo sequences in the archive cover reef life and marine subjects filmed for natural-history and travel productions that need location-accurate Indonesia imagery.",
            ],
            "bullets": [
                "Location-specific Komodo / Nusa Tenggara waters",
                "Cinema-camera underwater capture",
                "Rights-managed licensing with R3D masters",
            ],
        },
        {
            "slug": "sumbawa-stock-footage",
            "title": "Sumbawa Stock Footage",
            "h1": "Sumbawa & Sangeang Stock Footage",
            "description": (
                "License Sumbawa stock footage — rights-managed cultural and coastal cinema from "
                "Sangeang Island and Bontoh village, available as R3D."
            ),
            "keywords": (
                "Sumbawa stock footage, Sangeang Island video, Bontoh village footage, "
                "Sumbawa Indonesia film footage"
            ),
            "match": match_region("Sumbawa"),
            "limit": 48,
            "paragraphs": [
                "Sumbawa clips in the archive were filmed around Sangeang Island and Bontoh village: boat building, village life, coastal landscape, and related editorial scenes from eastern Indonesia.",
            ],
            "bullets": [
                "Sangeang Island and Bontoh village cultural scenes",
                "Coastal and village context for documentary B-roll",
                "Rights-managed licensing; many clips are editorial / no model release",
            ],
        },
    ]


REGION_COLLECTION_SLUGS = {
    "raja-ampat-stock-footage",
    "cenderawasih-stock-footage",
    "komodo-stock-footage",
    "sumbawa-stock-footage",
}


def build_collection_page(
    defn: CollectionDef,
    matched: list[dict],
    all_defs: list[CollectionDef],
    take_labels: dict[str, str] | None = None,
) -> str:
    cards = "".join(clip_card_html(c, take_labels) for c in matched[: defn.get("limit", 48)])
    bullets = "".join(f"<li>{esc(b)}</li>" for b in defn.get("bullets") or [])
    paragraphs = "".join(f"<p>{esc(p)}</p>" for p in defn.get("paragraphs") or [])
    others = [d for d in all_defs if d["slug"] != defn["slug"]]
    if defn["slug"] in REGION_COLLECTION_SLUGS:
        region_others = [d for d in others if d["slug"] in REGION_COLLECTION_SLUGS]
        rest = [d for d in others if d["slug"] not in REGION_COLLECTION_SLUGS]
        others = region_others + rest
    others = others[:6]
    other_links = "".join(
        f'<li><a href="/collections/{esc(d["slug"])}/">{esc(d["title"])}</a></li>'
        for d in others
    )
    body = f"""
  <main>
    <div class="layout-rail">
      <nav class="breadcrumbs" aria-label="Breadcrumb">
        <a href="/">Home</a><span>/</span>
        <a href="/collections/">Collections</a><span>/</span>
        <span>{esc(defn["title"])}</span>
      </nav>
      <p class="kicker">SEO collection</p>
      <h1 class="page-title">{esc(defn["h1"])}</h1>
      <p class="page-lead">{esc(defn["description"])}</p>
      <span class="badge">{len(matched)} clips · Rights Managed</span>

      <div class="prose">
        {paragraphs}
        <ul>{bullets}</ul>
        <p>Browse matching clips below, or <a href="/licensing-guide.html">read how licensing works</a> before you inquire.</p>
      </div>

      <div class="clip-grid">
        {cards}
      </div>

      <section class="related">
        <h2>Related collections</h2>
        <ul class="prose">{other_links}</ul>
      </section>
    </div>
  </main>
"""
    json_ld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": defn["h1"],
        "description": defn["description"],
        "url": collection_url(defn["slug"]),
        "isPartOf": {"@type": "WebSite", "name": SITE_NAME, "url": SITE},
        "about": defn["title"],
    }
    return page_shell(
        title=f"{defn['title']} | {SITE_NAME}",
        description=defn["description"],
        canonical=collection_url(defn["slug"]),
        body=body,
        json_ld=json_ld,
        active_nav="collections",
        keywords=defn.get("keywords"),
    )


def build_collections_hub(defs: list[CollectionDef], counts: dict[str, int]) -> str:
    cards = "".join(
        f"""
      <a class="collection-card" href="/collections/{esc(d['slug'])}/">
        <h2>{esc(d['title'])}</h2>
        <p>{esc(d['description'])}</p>
        <p class="clip-card-meta" style="margin-top:0.65rem">{counts.get(d['slug'], 0)} clips</p>
      </a>
"""
        for d in defs
    )
    body = f"""
  <main>
    <div class="layout-rail">
      <nav class="breadcrumbs" aria-label="Breadcrumb">
        <a href="/">Home</a><span>/</span>
        <span>Collections</span>
      </nav>
      <p class="kicker">Keyword collections</p>
      <h1 class="page-title">License Indo-Pacific Stock Footage by Topic</h1>
      <p class="page-lead">Focused landing pages for producers searching to license R3D footage, underwater cinema, location-specific archives, and rights-managed wildlife film.</p>
      <div class="collection-list">
        {cards}
      </div>
    </div>
  </main>
"""
    return page_shell(
        title=f"Stock Footage Collections | {SITE_NAME}",
        description=(
            "Browse Indo Pacific Stock collections — license R3D footage, underwater cinema, "
            "Raja Ampat, Cenderawasih Bay, Komodo, Sumbawa, whale sharks, and rights-managed wildlife film."
        ),
        canonical=f"{SITE}/collections/",
        body=body,
        active_nav="collections",
        keywords="license R3D footage, underwater stock footage, Raja Ampat stock footage, rights managed wildlife",
        json_ld={
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": "Stock Footage Collections",
            "url": f"{SITE}/collections/",
            "isPartOf": {"@type": "WebSite", "name": SITE_NAME, "url": SITE},
        },
    )


def write_sitemap(clip_slugs: list[str], collection_slugs: list[str]) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls: list[tuple[str, str, str]] = [
        (f"{SITE}/", "weekly", "1.0"),
        (f"{SITE}/collections/", "weekly", "0.9"),
        (f"{SITE}/licensing-guide.html", "monthly", "0.8"),
        (f"{SITE}/inquire.html", "monthly", "0.8"),
        (f"{SITE}/terms.html", "yearly", "0.3"),
        (f"{SITE}/license-terms.html", "yearly", "0.3"),
        (f"{SITE}/privacy.html", "yearly", "0.3"),
    ]
    for slug in collection_slugs:
        urls.append((collection_url(slug), "weekly", "0.85"))
    for slug in clip_slugs:
        urls.append((clip_url(slug), "monthly", "0.7"))

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, freq, priority in urls:
        parts.append("  <url>")
        parts.append(f"    <loc>{esc(loc)}</loc>")
        parts.append(f"    <lastmod>{today}</lastmod>")
        parts.append(f"    <changefreq>{freq}</changefreq>")
        parts.append(f"    <priority>{priority}</priority>")
        parts.append("  </url>")
    parts.append("</urlset>")
    parts.append("")
    SITEMAP_PATH.write_text("\n".join(parts), encoding="utf-8")


def xml_text(value: object, limit: int | None = None) -> str:
    text = str(value or "").strip()
    if limit is not None:
        text = text[:limit]
    return esc(text)


def write_video_sitemap(clips: list[dict]) -> int:
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">',
    ]
    included = 0
    for clip in clips:
        slug = clip.get("slug")
        still = thumb_url(slug) if slug else ""
        content = clip.get("videoUrl") or ""
        if not slug or not still or not content:
            continue
        specs = clip.get("technicalSpecs") or {}
        title = clip.get("title") or slug
        description = clip.get("description") or title
        seconds = clip_duration_seconds(
            specs.get("duration"), specs.get("fps"), specs.get("durationSeconds")
        )
        upload = str(specs.get("date") or "2026-03-01")[:10]
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", upload):
            upload = "2026-03-01"
        parts.append("  <url>")
        parts.append(f"    <loc>{esc(clip_url(slug))}</loc>")
        parts.append("    <video:video>")
        parts.append(f"      <video:thumbnail_loc>{esc(still)}</video:thumbnail_loc>")
        parts.append(f"      <video:title>{xml_text(title, 100)}</video:title>")
        parts.append(
            f"      <video:description>{xml_text(description, 2048)}</video:description>"
        )
        parts.append(f"      <video:content_loc>{esc(content)}</video:content_loc>")
        if seconds:
            parts.append(f"      <video:duration>{int(round(seconds))}</video:duration>")
        parts.append(
            f"      <video:publication_date>{upload}T00:00:00+00:00</video:publication_date>"
        )
        parts.append("      <video:family_friendly>yes</video:family_friendly>")
        parts.append("      <video:requires_subscription>no</video:requires_subscription>")
        parts.append("      <video:live>no</video:live>")
        parts.append("    </video:video>")
        parts.append("  </url>")
        included += 1
    parts.append("</urlset>")
    parts.append("")
    VIDEO_SITEMAP_PATH.write_text("\n".join(parts), encoding="utf-8")
    return included


def write_robots() -> None:
    (ROOT / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {SITE}/sitemap.xml\n"
        f"Sitemap: {SITE}/video-sitemap.xml\n",
        encoding="utf-8",
    )


def redirect_html(dest_path: str, dest_url: str, label: str) -> str:
    """Client redirect page for GitHub Pages (no server 301s)."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="refresh" content="0; url={esc(dest_path)}" />
  <link rel="canonical" href="{esc(dest_url)}" />
  <title>Redirecting…</title>
  <script>location.replace({json.dumps(dest_path)});</script>
</head>
<body>
  <p>This page has moved to <a href="{esc(dest_path)}">{esc(label)}</a>.</p>
</body>
</html>
"""


def write_legacy_clip_redirects(clips: list[dict]) -> int:
    """Place HTML redirect pages at old camera-id clip URLs.

    GitHub Pages has no server-side 301s. Google already crawled at least one
    ID-only path (/clip/a006-a009-0413qe-v1-0003/). Every clip used to have
    that shape, so each needs a real file at the old path.
    """
    used_old: set[str] = set()
    current_slugs = {c.get("slug") for c in clips if c.get("slug")}
    written = 0

    for clip in clips:
        slug = clip.get("slug")
        old = camera_id_slug(clip)
        if not slug or not old or old == slug or old in current_slugs or old in used_old:
            continue
        used_old.add(old)
        dest_path = f"/clip/{slug}/"
        dest_url = clip_url(slug)
        out = CLIP_DIR / old / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            redirect_html(dest_path, dest_url, clip.get("title") or slug),
            encoding="utf-8",
        )
        written += 1

    redirects_file = ROOT / "_redirects"
    if redirects_file.exists():
        redirects_file.unlink()
    return written


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    catalog_data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    clips = catalog_data.get("clips") or []
    if not clips:
        raise SystemExit("No clips found in videos/catalog.json")

    # Ensure slug present
    for clip in clips:
        if not clip.get("slug"):
            specs = clip.get("technicalSpecs") or {}
            clip["slug"] = specs.get("slug")
        if not clip.get("slug"):
            raise SystemExit(f"Clip missing slug: {clip.get('title')}")

    print(f"Generating SEO pages for {len(clips)} clips…")
    reset_dir(CLIP_DIR)
    reset_dir(COLLECTIONS_DIR)
    take_labels = take_label_map(clips)

    for clip in clips:
        slug = clip["slug"]
        out = CLIP_DIR / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_clip_page(clip, clips, take_labels), encoding="utf-8")

    defs = collection_defs()
    counts: dict[str, int] = {}
    for defn in defs:
        matched = [c for c in clips if defn["match"](c)]
        # Prefer diversified order: keep catalog order but cap
        counts[defn["slug"]] = len(matched)
        out = COLLECTIONS_DIR / defn["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_collection_page(defn, matched, defs, take_labels), encoding="utf-8")
        print(f"  collection /collections/{defn['slug']}/ → {len(matched)} clips")

    (COLLECTIONS_DIR / "index.html").write_text(
        build_collections_hub(defs, counts), encoding="utf-8"
    )

    # Keep old 8K collection URL working for anyone who already indexed it.
    legacy = COLLECTIONS_DIR / "license-8k-raw-footage" / "index.html"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text(
        redirect_html(
            "/collections/license-r3d-footage/",
            f"{SITE}/collections/license-r3d-footage/",
            "License R3D Footage",
        ),
        encoding="utf-8",
    )

    write_sitemap([c["slug"] for c in clips], [d["slug"] for d in defs])
    video_count = write_video_sitemap(clips)
    write_robots()
    redirect_count = write_legacy_clip_redirects(clips)
    print(
        f"Wrote {len(clips)} clip pages, {len(defs)} collections, "
        f"sitemap.xml, video-sitemap.xml ({video_count} videos), "
        f"{redirect_count} camera-id clip redirect pages"
    )


if __name__ == "__main__":
    main()
