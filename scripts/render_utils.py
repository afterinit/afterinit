"""Shared, dependency-free helpers for the profile SVG renderers."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "activity.json"
STATUS_PATH = ROOT / "data" / "status.json"
ASSET_DIR = ROOT / "assets"

BG = "#050505"
PANEL = "#0A0A0A"
GRID = "#141414"
BORDER = "#333333"
MUTED = "#888888"
DIM = "#555555"
TEXT = "#FFFFFF"
ACCENT = "#A8BAC8"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_svg(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = content.strip() + "\n"
    path.write_text(normalized, encoding="utf-8", newline="\n")


def x(value: object) -> str:
    raw = str(value)
    xml_safe = "".join(
        char
        for char in raw
        if char in "\t\n\r" or 0x20 <= ord(char) <= 0xD7FF or 0xE000 <= ord(char) <= 0xFFFD
    )
    return escape(xml_safe, quote=True)


def clip(value: object | None, limit: int, fallback: str = "—") -> str:
    text = " ".join(str(value or fallback).split())
    if len(text) <= limit:
        return text
    return text[: max(1, limit - 1)].rstrip() + "…"


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def now_from(data: dict) -> datetime:
    return parse_time(data.get("generated_at")) or datetime.now(timezone.utc)


def timezone_from(status: dict):
    name = status.get("timezone", "UTC")
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return timezone.utc


def relative_time(value: str | None, reference: datetime) -> str:
    moment = parse_time(value)
    if moment is None:
        return "NO SIGNAL"
    seconds = max(0, int((reference - moment).total_seconds()))
    if seconds < 60:
        return "JUST NOW"
    if seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} MIN{'S' if minutes != 1 else ''} AGO"
    if seconds < 86400:
        hours = seconds // 3600
        return f"{hours} HR{'S' if hours != 1 else ''} AGO"
    days = seconds // 86400
    return f"{days} DAY{'S' if days != 1 else ''} AGO"


def activity_state(latest_at: str | None, reference: datetime) -> tuple[str, str]:
    moment = parse_time(latest_at)
    if moment is None:
        return "NO SIGNAL", DIM
    hours = max(0, (reference - moment).total_seconds()) / 3600
    if hours < 1:
        return "ACTIVE", ACCENT
    if hours < 24:
        return "IDLE", MUTED
    return "OFFLINE", DIM


def format_local(value: str | None, tz, pattern: str = "%Y.%m.%d  /  %H:%M:%S") -> str:
    moment = parse_time(value)
    if moment is None:
        return "—"
    return moment.astimezone(tz).strftime(pattern)


def base_svg(width: int, height: int, body: str, *, title: str, animated: bool = False) -> str:
    scan = ""
    if animated:
        scan = f"""
  <rect class="scan" x="1" y="1" width="{width - 2}" height="1" fill="{ACCENT}" opacity="0.11">
    <animate attributeName="y" values="1;{height - 2};1" dur="16s" repeatCount="indefinite" />
  </rect>"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">{x(title)}</title>
  <desc id="desc">Generated from public GitHub activity by the repository workflow.</desc>
  <defs>
    <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
      <path d="M 24 0 L 0 0 0 24" fill="none" stroke="{GRID}" stroke-width="1" opacity="0.5" />
    </pattern>
    <style>
      .mono {{ font-family: 'IBM Plex Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', monospace; }}
      .label {{ fill: {MUTED}; font-size: 12px; letter-spacing: 2px; }}
      .micro {{ fill: {DIM}; font-size: 10px; letter-spacing: 1.4px; }}
      .value {{ fill: {TEXT}; font-size: 15px; }}
      .soft {{ fill: {MUTED}; font-size: 13px; }}
      .cursor {{ animation: blink 1.25s steps(1, end) infinite; }}
      @keyframes blink {{ 0%, 47% {{ opacity: 1; }} 48%, 100% {{ opacity: 0; }} }}
      @media (prefers-reduced-motion: reduce) {{ .cursor, .scan {{ animation: none; }} }}
    </style>
  </defs>
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" fill="{BG}" stroke="{BORDER}" />
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" fill="url(#grid)" />
{body}
{scan}
</svg>"""


def line(x1: int, y1: int, x2: int, y2: int, color: str = BORDER, opacity: float = 1) -> str:
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" opacity="{opacity}" />'


def text(x_pos: int, y_pos: int, value: object, css: str = "value", **attrs: object) -> str:
    extra = " ".join(f'{key.replace("_", "-")}="{x(val)}"' for key, val in attrs.items())
    return f'<text class="mono {css}" x="{x_pos}" y="{y_pos}" {extra}>{x(value)}</text>'


def bounded_signal(value: int, maximum: int, cells: int) -> int:
    if value <= 0 or maximum <= 0:
        return 0
    return max(1, min(cells, math.ceil((value / maximum) * cells)))
