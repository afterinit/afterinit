"""Render an angular editorial profile with restrained, linear motion."""

from __future__ import annotations

import hashlib
import re

from render_utils import (
    ASSET_DIR,
    DATA_PATH,
    ROOT,
    STATUS_PATH,
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
HEIGHT = 550

BACKGROUND = "#0B0C0D"
WHITE = "#E7E5DF"
GRAY = "#989995"
QUIET = "#70726F"
RULE = "#303230"
ACCENT = "#A89B7E"

# Each contour uses only horizontal, vertical, and 45-degree edges.
UPPER = (
    "M 764 156 L 808 112 H 1080 V 288 L 1036 332 "
    "H 922 V 280 H 1012 L 1028 264 V 164 H 836 "
    "L 816 184 V 280 H 764 Z"
)
LOWER = "M 838 208 H 890 V 340 H 1008 L 956 392 H 838 Z"


def update_readme_cache_key(svg: str) -> None:
    """Version the README image URL using the exact generated file bytes."""
    readme = ROOT / "README.md"
    source = readme.read_text(encoding="utf-8")
    cache_key = hashlib.sha256(svg.encode("utf-8")).hexdigest()[:12]
    pattern = re.compile(r"(\./assets/telemetry\.svg)(?:\?v=[^\"]+)?")
    updated, count = pattern.subn(
        lambda match: f"{match.group(1)}?v={cache_key}", source
    )
    if count == 0:
        raise RuntimeError("README telemetry image reference was not found")
    if updated != source:
        readme.write_text(updated, encoding="utf-8", newline="\n")


def weekly_signal(raw_days: object) -> str:
    days = raw_days[-7:] if isinstance(raw_days, list) else []
    days = [{"commits": 0}] * (7 - len(days)) + days
    values = [max(0, int(day.get("commits") or 0)) for day in days]
    maximum = max(values, default=0)
    segments = []
    for index, value in enumerate(values):
        start = 920 + index * 28
        height = 3 if not value else 6 + round(20 * value / maximum)
        fill = WHITE if value else RULE
        segments.append(
            f'<rect x="{start}" y="{450 - height}" width="18" height="{height}" '
            f'fill="{fill}"><title>{x(day_label(days[index], value))}</title></rect>'
        )
    return "\n      ".join(segments)


def day_label(day: dict, commits: int) -> str:
    return f"{day.get('date') or 'No date'} / {commits} public commits"


def render(data: dict, status: dict) -> str:
    now = now_from(data)
    tz = timezone_from(status)
    timezone_label = str(status.get("timezone_label") or "UTC")
    stats = data.get("stats") or {}
    push = data.get("latest_push") or {}
    repository = clip(push.get("repo"), 30, "Awaiting public activity")
    branch = clip(push.get("branch"), 16, "—")
    pushed_ago = relative_time(push.get("timestamp"), now).lower()
    commits = max(0, int(stats.get("commits") or 0))
    synced_at = format_local(data.get("generated_at"), tz, "%m.%d / %H:%M")
    username = clip(data.get("username"), 25, "afterinit")
    signal = weekly_signal(stats.get("daily"))
    tempo = 9 if commits > 15 else 12

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">Angular engineering profile for {x(username)}</title>
  <desc id="desc">Think clearly. Build precisely. Java backend engineering. Last public push: {x(repository)} / {x(branch)}, {x(pushed_ago)}. {commits} public commits in seven days. Updated {x(synced_at)} {x(timezone_label)}.</desc>
  <defs>
    <clipPath id="upper-cut"><path d="{UPPER}" /></clipPath>
    <clipPath id="lower-cut"><path d="{LOWER}" /></clipPath>
    <style>
      .sans {{ font-family: Arial, Helvetica, sans-serif; }}
      .mono {{ font-family: Consolas, 'Liberation Mono', monospace; }}
      .title {{ fill: {WHITE}; font-size: 62px; font-weight: 400; letter-spacing: -2.4px; }}
      .label {{ fill: {GRAY}; font-size: 11px; letter-spacing: 1.3px; }}
      .data {{ fill: {WHITE}; font-size: 17px; }}
      .muted {{ fill: {GRAY}; font-size: 13px; }}
      .foot {{ fill: {QUIET}; font-size: 10px; letter-spacing: 0.45px; }}
      .scan {{ animation: scan {tempo}s ease-in-out infinite; }}
      .trace {{ animation: trace 14s linear infinite; }}
      .transfer {{ animation: transfer 8s ease-in-out infinite; }}
      @keyframes scan {{
        0%, 16% {{ transform: translateY(0); opacity: 0; }}
        25% {{ opacity: 0.55; }}
        70% {{ opacity: 0.55; }}
        84%, 100% {{ transform: translateY(250px); opacity: 0; }}
      }}
      @keyframes trace {{
        0%, 10% {{ stroke-dashoffset: 0; opacity: 0; }}
        20%, 80% {{ opacity: 0.8; }}
        90%, 100% {{ stroke-dashoffset: -1024; opacity: 0; }}
      }}
      @keyframes transfer {{
        0%, 12% {{ transform: translateX(0); opacity: 0; }}
        20%, 72% {{ opacity: 0.6; }}
        88%, 100% {{ transform: translateX(1072px); opacity: 0; }}
      }}
      @media (prefers-reduced-motion: reduce) {{
        .scan, .trace, .transfer {{ animation: none; opacity: 0; }}
      }}
    </style>
  </defs>

  <rect width="{WIDTH}" height="{HEIGHT}" fill="{BACKGROUND}" />

  <!-- Typography and negative space define the composition. -->
  <text class="sans label" x="72" y="76">JAVA / BACKEND ENGINEERING</text>
  <text class="sans title" x="68" y="181">Think clearly.</text>
  <text class="sans title" x="68" y="252">Build precisely.</text>
  <text class="sans muted" x="72" y="303">Architecture. Code. Iteration.</text>

  <!-- Two interlocking cut components, without curves or surface effects. -->
  <g transform="translate(0 -24)">
  <path d="{UPPER}" fill="#242625" transform="translate(12 12)" />
  <path d="{LOWER}" fill="#191B1A" transform="translate(12 12)" />
  <path d="{UPPER}" fill="{WHITE}" />
  <path d="{LOWER}" fill="#6D706C" />
  <path d="M 838 340 H 890 L 856 374 H 838 Z" fill="{ACCENT}" />

  <!-- Light traverses a single straight axis; a small trace follows hard edges. -->
  <g clip-path="url(#upper-cut)">
    <rect class="scan" x="750" y="104" width="340" height="3" fill="{BACKGROUND}" opacity="0" />
  </g>
  <g clip-path="url(#lower-cut)">
    <rect class="scan" x="832" y="104" width="188" height="3" fill="{WHITE}" opacity="0" />
  </g>
  <path class="trace" d="M 792 252 V 168 L 822 138 H 1054 V 276 L 1024 306 H 940"
        fill="none" stroke="{BACKGROUND}" stroke-width="2"
        stroke-linejoin="miter" stroke-linecap="butt" pathLength="1024"
        stroke-dasharray="42 982" opacity="0" />
  </g>

  <!-- One compact row carries the actual public activity. -->
  <line x1="72" y1="395" x2="1128" y2="395" stroke="{RULE}" />
  <rect class="transfer" x="72" y="394" width="24" height="2" fill="{WHITE}" opacity="0" />
  <text class="sans label" x="72" y="425">LAST PUSH</text>
  <text class="sans data" x="72" y="452">{x(repository)}</text>
  <text class="mono muted" x="374" y="451">/ {x(branch)}</text>
  <text class="sans muted" x="622" y="451">{x(pushed_ago)}</text>

  <text class="sans label" x="1106" y="425" text-anchor="end">LAST 7 DAYS</text>
  {signal}
  <text class="sans muted" x="1106" y="474" text-anchor="end">{commits} public commits</text>

  <text class="sans foot" x="72" y="514">{x(username)} / public GitHub activity</text>
  <text class="mono foot" x="1128" y="514" text-anchor="end">updated {x(synced_at)} {x(timezone_label)}</text>
</svg>"""
    return svg.strip() + "\n"


def main() -> None:
    svg = render(read_json(DATA_PATH), read_json(STATUS_PATH))
    write_svg(ASSET_DIR / "telemetry.svg", svg)
    update_readme_cache_key(svg)


if __name__ == "__main__":
    main()
