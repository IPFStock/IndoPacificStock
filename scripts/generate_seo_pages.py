#!/usr/bin/env python3
"""Generate crawlable clip pages, keyword landings, and sitemap.xml from catalog.json."""

from __future__ import annotations

import html
import json
import re
import shutil
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

SHARED_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #F8FAFC; --surface: #FFFFFF; --border: #E6E8EA; --text: #0F172A;
  --text-secondary: #334155; --muted: #64748b; --accent: #059669;
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
.logo-icon { width: 1.25rem; height: 1.25rem; display: block; flex-shrink: 0; }
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
  border: 1px solid rgba(5, 150, 105, 0.35); background: rgba(5, 150, 105, 0.08);
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
.btn-primary:hover { background: #047857; border-color: #047857; }
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
.clip-card:hover { border-color: rgba(5, 150, 105, 0.45); transform: translateY(-1px); }
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
.collection-card:hover { border-color: rgba(5, 150, 105, 0.45); }
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
<svg class="logo-icon" viewBox="0 0 38 38" fill="none" aria-hidden="true">
  <circle cx="19" cy="19" r="17" stroke="#059669" stroke-width="1" opacity="0.25"/>
  <circle cx="19" cy="19" r="11.5" stroke="#059669" stroke-width="1.2" opacity="0.75"/>
  <path d="M19 7.5v23M7.5 19h23" stroke="#059669" stroke-width="0.75" opacity="0.45"/>
  <circle cx="19" cy="19" r="3.5" fill="#059669" opacity="0.9"/>
  <path d="M8 26 Q19 30 30 26" stroke="#059669" stroke-width="0.8" opacity="0.35" fill="none"/>
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


def clip_url(slug: str) -> str:
    return f"{SITE}/clip/{slug}/"


def collection_url(slug: str) -> str:
    return f"{SITE}/collections/{slug}/"


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


def iso8601_duration(duration: object, fps: object = None, duration_seconds: object = None) -> str:
    """Convert catalog clip length to schema.org / Google ISO 8601 duration (PT#H#M#S)."""
    total: float | None = None
    try:
        if duration_seconds not in (None, ""):
            parsed = float(duration_seconds)
            if parsed > 0:
                total = parsed
    except (TypeError, ValueError):
        total = None

    raw = str(duration or "").strip()
    if total is None and raw:
        if re.match(r"^PT(?=\d)(?:\d+H)?(?:\d+M)?(?:\d+(?:\.\d+)?S)?$", raw, re.I):
            return raw.upper()

        match = re.match(r"^(\d+):(\d{1,2}):(\d{1,2})(?::(\d{1,3}))?$", raw)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            frames = int(match.group(4) or 0)
            frame_rate = parse_fps(fps)
            total = hours * 3600 + minutes * 60 + seconds + (frames / frame_rate if frames else 0)
        else:
            try:
                parsed = float(raw)
                if parsed > 0:
                    total = parsed
            except ValueError:
                total = None

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
        <a href="mailto:licensingips@gmail.com" class="inquire-link">Inquire</a>
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
    active_nav: str | None = None,
    keywords: str | None = None,
) -> str:
    keywords_tag = (
        f'  <meta name="keywords" content="{esc(keywords)}" />\n' if keywords else ""
    )
    ld = ""
    if json_ld is not None:
        ld = (
            '  <script type="application/ld+json">\n'
            f"  {json.dumps(json_ld, ensure_ascii=False)}\n"
            "  </script>\n"
        )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}" />
{keywords_tag}  <link rel="canonical" href="{esc(canonical)}" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:type" content="{esc(og_type)}" />
  <meta property="og:url" content="{esc(canonical)}" />
  <meta property="og:site_name" content="{esc(SITE_NAME)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(title)}" />
  <meta name="twitter:description" content="{esc(description)}" />
{ld}  <style>{SHARED_CSS}</style>
</head>
<body>
{header_html(active_nav)}
{body}
{footer_html()}
</body>
</html>
"""


def clip_card_html(clip: dict) -> str:
    slug = clip["slug"]
    title = clip.get("title") or slug
    desc = clip.get("description") or ""
    meta_bits = [clip.get("region"), clip.get("nativeFormatBadge") or clip.get("format"), "Rights Managed"]
    meta = " · ".join(bit for bit in meta_bits if bit)
    video = clip.get("videoUrl") or ""
    return f"""
    <a class="clip-card" href="/clip/{esc(slug)}/">
      <div class="clip-card-media">
        <video muted preload="metadata" playsinline src="{esc(video)}"></video>
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


def build_clip_page(clip: dict, catalog: list[dict]) -> str:
    slug = clip["slug"]
    title = clip.get("title") or slug
    description = clip.get("description") or (
        f"{title} — rights-managed Indo-Pacific stock footage available to license as R3D."
    )
    page_title = f"{title} | License R3D Stock Footage | {SITE_NAME}"
    meta_desc = description[:155] + ("…" if len(description) > 155 else "")
    specs = clip.get("technicalSpecs") or {}
    keywords = clip.get("keywords") or []
    keyword_str = ", ".join(keywords[:24])
    inquire = (
        "mailto:licensingips@gmail.com"
        f"?subject={quote(f'License request: {title} ({slug})')}"
    )
    duration = specs.get("duration") or ""
    schema_duration = iso8601_duration(
        duration, specs.get("fps"), specs.get("durationSeconds")
    )
    upload = specs.get("date") or "2026-03-01"
    if not re.match(r"^\d{4}-\d{2}-\d{2}", str(upload)):
        upload = "2026-03-01"
    masters = master_delivery_label(clip)
    json_ld = {
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": title,
        "description": description,
        "thumbnailUrl": clip.get("videoUrl"),
        "contentUrl": clip.get("videoUrl"),
        "uploadDate": f"{str(upload)[:10]}T00:00:00Z",
        "keywords": keywords[:30],
        "author": {"@type": "Organization", "name": SITE_NAME},
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE},
        "isFamilyFriendly": True,
        "license": f"{SITE}/license-terms.html",
        "encodingFormat": "video/r3d",
    }
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
        ("License", "Rights Managed (RM)"),
        ("Available masters", masters),
    ]:
        if value:
            specs_rows.append(f"<dt>{esc(label)}</dt><dd>{esc(value)}</dd>")

    related = related_clips(clip, catalog)
    related_html = "".join(clip_card_html(item) for item in related)

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
          <video controls playsinline preload="metadata" src="{esc(clip.get('videoUrl'))}"
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
    ]


def build_collection_page(defn: CollectionDef, matched: list[dict], all_defs: list[CollectionDef]) -> str:
    cards = "".join(clip_card_html(c) for c in matched[: defn.get("limit", 48)])
    bullets = "".join(f"<li>{esc(b)}</li>" for b in defn.get("bullets") or [])
    paragraphs = "".join(f"<p>{esc(p)}</p>" for p in defn.get("paragraphs") or [])
    others = [
        d for d in all_defs if d["slug"] != defn["slug"]
    ][:6]
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
            "Raja Ampat, Komodo, whale sharks, and rights-managed wildlife film."
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

    for clip in clips:
        slug = clip["slug"]
        out = CLIP_DIR / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_clip_page(clip, clips), encoding="utf-8")

    defs = collection_defs()
    counts: dict[str, int] = {}
    for defn in defs:
        matched = [c for c in clips if defn["match"](c)]
        # Prefer diversified order: keep catalog order but cap
        counts[defn["slug"]] = len(matched)
        out = COLLECTIONS_DIR / defn["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_collection_page(defn, matched, defs), encoding="utf-8")
        print(f"  collection /collections/{defn['slug']}/ → {len(matched)} clips")

    (COLLECTIONS_DIR / "index.html").write_text(
        build_collections_hub(defs, counts), encoding="utf-8"
    )

    # Keep old 8K collection URL working for anyone who already indexed it.
    legacy = COLLECTIONS_DIR / "license-8k-raw-footage" / "index.html"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text(
        """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="refresh" content="0; url=/collections/license-r3d-footage/" />
  <link rel="canonical" href="https://indopacificstock.com/collections/license-r3d-footage/" />
  <title>Redirecting…</title>
  <script>location.replace("/collections/license-r3d-footage/");</script>
</head>
<body>
  <p>This page has moved to <a href="/collections/license-r3d-footage/">License R3D Footage</a>.</p>
</body>
</html>
""",
        encoding="utf-8",
    )

    write_sitemap([c["slug"] for c in clips], [d["slug"] for d in defs])
    print(f"Wrote {len(clips)} clip pages, {len(defs)} collections, sitemap.xml")


if __name__ == "__main__":
    main()
