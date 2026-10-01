"""Render a generative spectrum sculpture from public GitHub activity."""

from __future__ import annotations

import math

from render_utils import (
    ASSET_DIR,
    DATA_PATH,
    DIM,
    STATUS_PATH,
    activity_state,
    clip,
    format_local,
    now_from,
    read_json,
    relative_time,
    timezone_from,
    write_svg,
    x,
)


WIDTH = 1200
HEIGHT = 720

INK = "#030406"
TEXT = "#F0EFEC"
MUTED = "#8C8B91"
DIM_TEXT = "#55575F"
BORDER = "#292B32"
TEAL = "#719B9D"
BLUE = "#6D7DA4"
VIOLET = "#857397"
PLUM = "#987184"
COPPER = "#A27F68"
GOLD = "#A18E68"
PEARL = "#C9D1CF"


def normalized_days(raw_days: object) -> list[dict]:
    days = raw_days[-7:] if isinstance(raw_days, list) else []
    return ([{"day": "--", "date": "", "commits": 0}] * (7 - len(days))) + days


def smooth_parts(points: list[tuple[float, float]]) -> tuple[str, list[str]]:
    start = f"M {points[0][0]:.1f} {points[0][1]:.1f}"
    segments: list[str] = []
    for index in range(len(points) - 1):
        p0 = points[max(0, index - 1)]
        p1 = points[index]
        p2 = points[index + 1]
        p3 = points[min(len(points) - 1, index + 2)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        segments.append(
            f"C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
        )
    return start, segments


def smooth_path(points: list[tuple[float, float]]) -> str:
    start, segments = smooth_parts(points)
    return " ".join([start, *segments])


def shifted(points: list[tuple[float, float]], offset: float) -> list[tuple[float, float]]:
    return [(px, py + offset) for px, py in points]


def ribbon_path(upper: list[tuple[float, float]], lower: list[tuple[float, float]]) -> str:
    start, upper_segments = smooth_parts(upper)
    lower_reversed = list(reversed(lower))
    _, lower_segments = smooth_parts(lower_reversed)
    join = f"L {lower_reversed[0][0]:.1f} {lower_reversed[0][1]:.1f}"
    return " ".join([start, *upper_segments, join, *lower_segments, "Z"])


def sculpture(days: list[dict]) -> tuple[str, str, str, list[tuple[float, float]]]:
    values = [max(0, int(day.get("commits") or 0)) for day in days]
    maximum = max(values, default=0)
    extended = [0, *values, 0]
    base: list[tuple[float, float]] = []
    alternate: list[tuple[float, float]] = []
    for index, value in enumerate(extended):
        px = -40 + index * 160
        ratio = value / maximum if maximum else 0
        py = 388 - index * 9 + math.sin(index * 1.18) * 30 - ratio * 70
        base.append((px, py))
        alternate.append((px, py + math.cos(index * 1.07) * 22))

    palette = (TEAL, BLUE, VIOLET, PLUM, COPPER, GOLD, TEAL, VIOLET)
    offsets = (-76, -53, -34, -17, 0, 20, 43, 70)
    lines: list[str] = []
    for index, (offset, color) in enumerate(zip(offsets, palette)):
        first = smooth_path(shifted(base, offset))
        second = smooth_path(shifted(alternate, offset))
        opacity = 0.18 + index * 0.035
        width = 0.8 if index not in (3, 4) else 1.25
        dash = ' stroke-dasharray="8 13"' if index in (1, 6) else ""
        dash_animation = (
            f'<animate attributeName="stroke-dashoffset" values="126;0;-126" '
            f'dur="{18 + index}s" repeatCount="indefinite" />'
            if dash
            else ""
        )
        lines.append(
            f'<path d="{first}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'opacity="{opacity:.2f}"{dash}>'
            f'<animate attributeName="d" values="{first};{second};{first}" '
            f'dur="{15 + index * 1.3:.1f}s" repeatCount="indefinite" />'
            f'{dash_animation}</path>'
        )

    upper_base = shifted(base, -20)
    lower_base = shifted(base, 20)
    upper_alt = shifted(alternate, -20)
    lower_alt = shifted(alternate, 20)
    band_first = ribbon_path(upper_base, lower_base)
    band_second = ribbon_path(upper_alt, lower_alt)
    center_path = smooth_path(base)
    return "".join(lines), band_first, band_second, base


def facets(points: list[tuple[float, float]], days: list[dict]) -> str:
    colors = (TEAL, BLUE, VIOLET, PLUM, COPPER, GOLD, TEAL)
    output: list[str] = []
    for index in range(1, 8):
        current = points[index]
        following = points[index + 1]
        value = max(0, int(days[index - 1].get("commits") or 0))
        color = colors[index - 1]
        opacity = 0.065 if value == 0 else 0.11 + min(value, 8) * 0.008
        polygon = (
            f"{current[0] - 8:.1f},{current[1] - 29:.1f} "
            f"{following[0] + 8:.1f},{following[1] - 15:.1f} "
            f"{following[0] - 15:.1f},{following[1] + 30:.1f} "
            f"{current[0] + 17:.1f},{current[1] + 38:.1f}"
        )
        output.append(
            f'<polygon points="{polygon}" fill="{color}" stroke="{color}" stroke-opacity="0.24" '
            f'opacity="{opacity:.3f}">'
            f'<animate attributeName="opacity" values="{opacity * 0.62:.3f};{opacity * 1.35:.3f};'
            f'{opacity * 0.62:.3f}" dur="{6.2 + index * 0.7:.1f}s" '
            f'begin="{-index * 0.8:.1f}s" repeatCount="indefinite" /></polygon>'
        )
    return "".join(output)


def activity_track(days: list[dict]) -> str:
    colors = (TEAL, BLUE, VIOLET, PLUM, COPPER, GOLD, TEAL)
    output: list[str] = []
    for index, day in enumerate(days):
        start = 64 + index * 153
        value = max(0, int(day.get("commits") or 0))
        color = colors[index] if value else BORDER
        opacity = 0.82 if value else 0.38
        output.append(
            f'<line x1="{start}" y1="504" x2="{start + 130}" y2="504" stroke="{color}" '
            f'stroke-width="2" opacity="{opacity}" />'
            f'<rect x="{start}" y="500" width="8" height="8" fill="{color}" opacity="{opacity}">'
            f'<animate attributeName="opacity" values="{opacity * 0.45:.2f};{opacity:.2f};{opacity * 0.45:.2f}" '
            f'dur="4s" begin="{index * 0.3:.1f}s" repeatCount="indefinite" /></rect>'
            f'<text class="mono nano" x="{start}" y="527" style="fill:{color}">'
            f'{x(day.get("day", "--"))} / {value:02d}</text>'
        )
    return "".join(output)


def main() -> None:
    data = read_json(DATA_PATH)
    status = read_json(STATUS_PATH)
    now = now_from(data)
    tz = timezone_from(status)
    timezone_label = status.get("timezone_label", "UTC")
    events = data.get("events") or []
    stats = data.get("stats") or {}
    push = data.get("latest_push")
    latest_at = events[0].get("timestamp") if events else None
    state, _ = activity_state(latest_at, now)
    state_color = {
        "ACTIVE": TEAL,
        "IDLE": GOLD,
        "OFFLINE": DIM_TEXT,
        "NO SIGNAL": DIM,
    }.get(state, DIM)
    commits = int(stats.get("commits") or 0)
    pushes = int(stats.get("pushes") or 0)
    days = normalized_days(stats.get("daily"))
    flowing_lines, band_first, band_second, points = sculpture(days)
    facet_shapes = facets(points, days)
    track = activity_track(days)
    center_path = smooth_path(points)
    motion_path = smooth_path(
        [(px - points[0][0], py - points[0][1]) for px, py in points]
    )

    if push:
        repository = clip(push.get("repo"), 34)
        branch = clip(push.get("branch"), 20)
        message = clip(push.get("message"), 72)
        pushed_at = format_local(push.get("timestamp"), tz, "%Y.%m.%d  /  %H:%M:%S")
        pushed_ago = relative_time(push.get("timestamp"), now)
    else:
        repository = "AWAITING FIRST PUBLIC PUSH"
        branch = "—"
        message = "RUN THE TELEMETRY WORKFLOW TO ESTABLISH SIGNAL"
        pushed_at = "—"
        pushed_ago = "NO SIGNAL"

    tagline = clip(status.get("tagline"), 70)
    synced_at = format_local(data.get("generated_at"), tz, "%Y.%m.%d  %H:%M")

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">afterinit generative activity spectrum</title>
  <desc id="desc">A flowing spectrum sculpture shaped by seven days of public GitHub activity.</desc>
  <defs>
    <linearGradient id="surface" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#06090A" />
      <stop offset="0.46" stop-color="{INK}" />
      <stop offset="1" stop-color="#0A0608" />
    </linearGradient>
    <linearGradient id="spectrum" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{TEAL}">
        <animate attributeName="stop-color" values="{TEAL};{BLUE};{TEAL}" dur="18s" repeatCount="indefinite" />
      </stop>
      <stop offset="0.34" stop-color="{BLUE}" />
      <stop offset="0.56" stop-color="{VIOLET}">
        <animate attributeName="stop-color" values="{VIOLET};{PLUM};{VIOLET}" dur="16s" repeatCount="indefinite" />
      </stop>
      <stop offset="0.78" stop-color="{PLUM}" />
      <stop offset="1" stop-color="{COPPER}" />
    </linearGradient>
    <linearGradient id="bandFill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{TEAL}" stop-opacity="0.08" />
      <stop offset="0.5" stop-color="{VIOLET}" stop-opacity="0.30" />
      <stop offset="1" stop-color="{PLUM}" stop-opacity="0.04" />
    </linearGradient>
    <radialGradient id="auraLeft" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="{TEAL}" stop-opacity="0.16" />
      <stop offset="1" stop-color="{TEAL}" stop-opacity="0" />
    </radialGradient>
    <radialGradient id="auraRight" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="{PLUM}" stop-opacity="0.15" />
      <stop offset="1" stop-color="{PLUM}" stop-opacity="0" />
    </radialGradient>
    <pattern id="grain" width="64" height="64" patternUnits="userSpaceOnUse">
      <path d="M 64 0 L 0 0 0 64" fill="none" stroke="#15171C" stroke-width="1" opacity="0.34" />
    </pattern>
    <filter id="glow" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="5" result="blur" />
      <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
    </filter>
    <filter id="soft" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur stdDeviation="24" />
    </filter>
    <style>
      .mono {{ font-family: 'IBM Plex Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', monospace; }}
      .cap {{ fill: {MUTED}; font-size: 11px; letter-spacing: 2.5px; }}
      .micro {{ fill: {DIM_TEXT}; font-size: 10px; letter-spacing: 1.4px; }}
      .nano {{ fill: #484A52; font-size: 8px; letter-spacing: 1.1px; }}
      .body {{ fill: #A09FA4; font-size: 13px; }}
      .cursor {{ animation: blink 1.2s steps(1, end) infinite; }}
      @keyframes blink {{ 0%, 46% {{ opacity: 1; }} 47%, 100% {{ opacity: 0; }} }}
      @media (prefers-reduced-motion: reduce) {{ .cursor {{ animation: none; }} }}
    </style>
  </defs>

  <rect x="0.5" y="0.5" width="1199" height="719" fill="url(#surface)" stroke="{BORDER}" />
  <rect x="1" y="1" width="1198" height="718" fill="url(#grain)" opacity="0.34" />
  <ellipse cx="180" cy="348" rx="330" ry="285" fill="url(#auraLeft)" opacity="0.72" filter="url(#soft)">
    <animate attributeName="opacity" values="0.48;0.82;0.48" dur="14s" repeatCount="indefinite" />
  </ellipse>
  <ellipse cx="1010" cy="324" rx="360" ry="300" fill="url(#auraRight)" opacity="0.72" filter="url(#soft)">
    <animate attributeName="opacity" values="0.78;0.46;0.78" dur="17s" repeatCount="indefinite" />
  </ellipse>

  <path d="M 18 46 V 18 H 46 M 1154 18 H 1182 V 46 M 18 674 V 702 H 46 M 1154 702 H 1182 V 674"
        fill="none" stroke="#353740" />
  <text class="mono nano" x="22" y="360" transform="rotate(-90 22 360)">GENERATIVE SIGNAL / PUBLIC GITHUB ACTIVITY</text>

  <!-- Editorial identity -->
  <text class="mono micro" x="62" y="43" style="fill:{TEAL}">AFTERINIT / DEV NODE 01</text>
  <text class="mono" x="60" y="105" fill="{TEXT}" font-size="59" font-weight="700" letter-spacing="8">AFTERINIT<tspan class="cursor" fill="{PEARL}">_</tspan></text>
  <text class="mono cap" x="63" y="140">{x(status.get('role', 'JAVA BACKEND / COMPUTER SCIENCE'))}</text>
  <text class="mono body" x="63" y="168">{x(tagline)}</text>
  <line x1="62" y1="188" x2="1138" y2="188" stroke="{BORDER}" />
  <line x1="62" y1="188" x2="225" y2="188" stroke="url(#spectrum)" stroke-width="2" />

  <text class="mono micro" x="1138" y="44" text-anchor="end">GITHUB SIGNAL</text>
  <rect x="1129" y="62" width="9" height="9" fill="{state_color}" filter="url(#glow)">
    <animate attributeName="opacity" values="0.3;1;0.3" dur="2.5s" repeatCount="indefinite" />
  </rect>
  <text class="mono" x="1115" y="73" fill="{TEXT}" font-size="18" letter-spacing="2" text-anchor="end">{x(state)}</text>
  <text class="mono micro" x="1138" y="104" text-anchor="end">{x(relative_time(latest_at, now))}</text>
  <text class="mono nano" x="1138" y="132" text-anchor="end">SYNC / {x(synced_at)} {x(timezone_label)}</text>

  <!-- Generative spectrum sculpture -->
  <g>
    {facet_shapes}
    <path d="{band_first}" fill="url(#bandFill)" stroke="none" opacity="0.86" filter="url(#glow)">
      <animate attributeName="d" values="{band_first};{band_second};{band_first}" dur="18s" repeatCount="indefinite" />
    </path>
    {flowing_lines}
    <path d="{center_path}" fill="none" stroke="url(#spectrum)" stroke-width="2" opacity="0.88"
          stroke-dasharray="22 15">
      <animate attributeName="stroke-dashoffset" values="370;0;-370" dur="15s" repeatCount="indefinite" />
    </path>
    <circle cx="{points[0][0]:.1f}" cy="{points[0][1]:.1f}" r="4" fill="{PEARL}" filter="url(#glow)">
      <animateMotion path="{motion_path}" dur="9s" repeatCount="indefinite" />
    </circle>
    <circle cx="{points[0][0]:.1f}" cy="{points[0][1]:.1f}" r="3" fill="{PLUM}" filter="url(#glow)">
      <animateMotion path="{motion_path}" dur="12s" begin="-5s" repeatCount="indefinite" />
    </circle>
    <circle cx="{points[0][0]:.1f}" cy="{points[0][1]:.1f}" r="2.5" fill="{TEAL}" filter="url(#glow)">
      <animateMotion path="{motion_path}" dur="15s" begin="-10s" repeatCount="indefinite" />
    </circle>
    <rect x="{points[4][0] - 3:.1f}" y="{points[4][1] - 3:.1f}" width="6" height="6"
          fill="{PEARL}" opacity="0.54" transform="rotate(45 {points[4][0]:.1f} {points[4][1]:.1f})">
      <animate attributeName="opacity" values="0.28;0.82;0.28" dur="4.6s" repeatCount="indefinite" />
    </rect>
  </g>

  <!-- Seven-day sampling track -->
  {track}

  <!-- Minimal activity metadata -->
  <line x1="62" y1="554" x2="1138" y2="554" stroke="{BORDER}" />
  <text class="mono micro" x="62" y="581">LAST PUSH</text>
  <text class="mono" x="62" y="615" fill="{TEXT}" font-size="19">{x(repository)}</text>
  <text class="mono body" x="385" y="615">/ {x(branch)}</text>
  <text class="mono body" x="62" y="645">{x(message)}</text>

  <text class="mono micro" x="1138" y="581" text-anchor="end">ACTIVITY / 7D</text>
  <text class="mono" x="1138" y="615" fill="{TEXT}" font-size="19" text-anchor="end">{commits:02d} COMMITS  /  {pushes:02d} PUSHES</text>
  <text class="mono micro" x="1138" y="645" text-anchor="end">{x(pushed_at)} {x(timezone_label)}  /  {x(pushed_ago)}</text>

  <text class="mono nano" x="62" y="686">PUBLIC ACTIVITY / GENERATED EVERY 06H</text>
  <text class="mono nano" x="1138" y="686" text-anchor="end">ACTIVITY STATE IS NOT LIVE PRESENCE</text>
</svg>"""
    write_svg(ASSET_DIR / "telemetry.svg", svg)


if __name__ == "__main__":
    main()
