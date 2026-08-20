#!/usr/bin/env python3
"""Rasterize the Indo Pacific Stock mark into favicon and schema logo files."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SLATE = (15, 23, 42, 255)
EMERALD = (5, 150, 105, 255)
WHITE = (255, 255, 255, 255)


def _ellipse(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, **kwargs) -> None:
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), **kwargs)


def draw_mark(image: Image.Image, *, accent: tuple[int, int, int, int], include_wave: bool) -> None:
    draw = ImageDraw.Draw(image)
    size = image.size[0]
    cx = cy = size / 2
    scale = size / 32

    _ellipse(draw, cx, cy, 11.5 * scale, outline=accent[:3] + (160,), width=max(1, round(1.35 * scale)))
    _ellipse(draw, cx, cy, 7.8 * scale, outline=accent, width=max(2, round(1.7 * scale)))

    arm = 9.2 * scale
    width = max(1, round(1.15 * scale))
    draw.line((cx, cy - arm, cx, cy + arm), fill=accent[:3] + (178,), width=width)
    draw.line((cx - arm, cy, cx + arm, cy), fill=accent[:3] + (178,), width=width)
    _ellipse(draw, cx, cy, 2.6 * scale, fill=accent)

    if include_wave and size >= 32:
        points = []
        for i in range(21):
            t = i / 20
            x = cx + (-7.8 + 15.6 * t) * scale
            y = cy + (5.4 + 2.8 * (1 - 4 * (t - 0.5) ** 2)) * scale
            points.append((x, y))
        draw.line(points, fill=accent[:3] + (140,), width=width, joint="curve")


def render(size: int, background: tuple[int, int, int, int], include_wave: bool = True) -> Image.Image:
    image = Image.new("RGBA", (size, size), background)
    draw_mark(image, accent=EMERALD, include_wave=include_wave)
    return image


def main() -> None:
    images_dir = ROOT / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    icon = render(64, SLATE)
    icon.save(ROOT / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])

    render(180, SLATE).save(ROOT / "apple-touch-icon.png", format="PNG")
    render(512, WHITE).convert("RGB").save(images_dir / "logo.png", format="PNG")
    print("Wrote favicon.ico, apple-touch-icon.png, images/logo.png")


if __name__ == "__main__":
    main()
