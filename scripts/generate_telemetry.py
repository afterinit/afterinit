"""Render one restrained, animated activity signal for the profile README."""

from __future__ import annotations

from render_utils import (
    ASSET_DIR,
    BORDER,
    DATA_PATH,
    DIM,
    MUTED,
    STATUS_PATH,
    TEXT,
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
HEIGHT = 650
BASELINE = 255
ICE = "#8FA8B8"
SAGE = "#83958A"
SAND = "#A18F79"
SLATE = "#667781"


def build_signal_path(daily: list[dict]) -> str:
    """Create a sharp telemetry waveform whose amplitude follows daily commits."""
    values = [max(0, int(day.get("commits") or 0)) for day in daily[-7:]]
    if len(values) < 7:
        values = [0] * (7 - len(values)) + values
    maximum = max(values, default=0)
    left, right = 64, 1136
    segment = (right - left) / 7
    commands = [f"M {left} {BASELINE}"]

    for index, value in enumerate(values):
        center = left + segment * (index + 0.5)
        start = center - segment * 0.42
        end = center + segment * 0.42
        commands.append(f"L {start:.1f} {BASELINE}")
        if value > 0 and maximum > 0:
            amplitude = 16 + round((value / maximum) * 40)
            commands.extend(
                [
                    f"L {center - 22:.1f} {BASELINE}",
                    f"L {center - 9:.1f} {BASELINE - amplitude * 0.28:.1f}",
                    f"L {center:.1f} {BASELINE - amplitude}",
                    f"L {center + 9:.1f} {BASELINE + amplitude * 0.46:.1f}",
                    f"L {center + 19:.1f} {BASELINE}",
                ]
            )
        commands.append(f"L {end:.1f} {BASELINE}")
    commands.append(f"L {right} {BASELINE}")
    return " ".join(commands)


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
        "ACTIVE": SAGE,
        "IDLE": SAND,
        "OFFLINE": SLATE,
        "NO SIGNAL": DIM,
    }.get(state, DIM)
    daily = stats.get("daily") if isinstance(stats.get("daily"), list) else []
    signal_path = build_signal_path(daily)
    commits = int(stats.get("commits") or 0)

    if push:
        repository = clip(push.get("repo"), 32)
        branch = clip(push.get("branch"), 24)
        message = clip(push.get("message"), 88)
        pushed_at = format_local(push.get("timestamp"), tz, "%Y.%m.%d  /  %H:%M:%S")
        pushed_ago = relative_time(push.get("timestamp"), now)
    else:
        repository = "AWAITING FIRST PUBLIC PUSH"
        branch = "—"
        message = "RUN THE TELEMETRY WORKFLOW TO ESTABLISH SIGNAL"
        pushed_at = "—"
        pushed_ago = "NO SIGNAL"

    signal_days = daily[-7:]
    if len(signal_days) < 7:
        signal_days = ([{"day": "--", "commits": 0}] * (7 - len(signal_days))) + signal_days
    day_markers = []
    marker_colors = (ICE, SAGE, SAND, ICE, SAGE, SAND, ICE)
    segment = (1136 - 64) / 7
    for index, day in enumerate(signal_days):
        center = 64 + segment * (index + 0.5)
        value = max(0, int(day.get("commits") or 0))
        color = marker_colors[index] if value else DIM
        day_markers.append(
            f'<line x1="{center:.1f}" y1="275" x2="{center:.1f}" y2="284" stroke="{color}" opacity="0.55" />'
            f'<rect x="{center - 2:.1f}" y="286" width="4" height="4" fill="{color}" opacity="0.35">'
            f'<animate attributeName="opacity" values="0.25;0.9;0.25" dur="3.8s" '
            f'begin="{index * 0.3:.1f}s" repeatCount="indefinite" /></rect>'
            f'<text class="mono micro" x="{center:.1f}" y="307" text-anchor="middle" '
            f'style="fill:{color}">{x(day.get("day", "--"))} / {value:02d}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">afterinit developer activity signal</title>
  <desc id="desc">A monochrome animated signal generated from recent public GitHub activity.</desc>
  <defs>
    <linearGradient id="surface" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#070A0C" />
      <stop offset="0.52" stop-color="#050606" />
      <stop offset="1" stop-color="#090806" />
    </linearGradient>
    <linearGradient id="signalColor" x1="64" y1="0" x2="1136" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{ICE}" />
      <stop offset="0.52" stop-color="{SAGE}" />
      <stop offset="1" stop-color="{SAND}" />
    </linearGradient>
    <linearGradient id="pipelineColor" x1="64" y1="0" x2="1136" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{ICE}" stop-opacity="0.55" />
      <stop offset="0.5" stop-color="{SAGE}" stop-opacity="0.55" />
      <stop offset="1" stop-color="{SAND}" stop-opacity="0.55" />
    </linearGradient>
    <pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse">
      <path d="M 48 0 L 0 0 0 48" fill="none" stroke="#151515" stroke-width="1" opacity="0.46" />
    </pattern>
    <style>
      .mono {{ font-family: 'IBM Plex Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', monospace; }}
      .cap {{ fill: {MUTED}; font-size: 11px; letter-spacing: 2.4px; }}
      .micro {{ fill: {DIM}; font-size: 10px; letter-spacing: 1.35px; }}
      .body {{ fill: {MUTED}; font-size: 14px; }}
      .cursor {{ animation: blink 1.2s steps(1, end) infinite; }}
      @keyframes blink {{ 0%, 46% {{ opacity: 1; }} 47%, 100% {{ opacity: 0; }} }}
      @media (prefers-reduced-motion: reduce) {{ .cursor {{ animation: none; }} }}
    </style>
  </defs>

  <rect x="0.5" y="0.5" width="1199" height="649" fill="url(#surface)" stroke="{BORDER}" />
  <rect x="1" y="141" width="1198" height="418" fill="url(#grid)" opacity="0.42" />

  <path d="M 18 42 V 18 H 42 M 1158 18 H 1182 V 42 M 18 608 V 632 H 42 M 1158 632 H 1182 V 608"
        fill="none" stroke="{BORDER}" />

  <text class="mono" x="64" y="76" fill="{TEXT}" font-size="47" font-weight="700" letter-spacing="6">AFTERINIT<tspan class="cursor" fill="{ACCENT}">_</tspan></text>
  <text class="mono cap" x="66" y="109">{x(status.get('role', 'JAVA BACKEND / COMPUTER SCIENCE'))}</text>

  <text class="mono micro" x="1136" y="46" text-anchor="end">GITHUB / PUBLIC ACTIVITY</text>
  <rect x="1127" y="61" width="9" height="9" fill="{state_color}">
    <animate attributeName="opacity" values="0.25;1;0.25" dur="2.4s" repeatCount="indefinite" />
  </rect>
  <text class="mono" x="1112" y="72" fill="{TEXT}" font-size="18" letter-spacing="2" text-anchor="end">{x(state)}</text>
  <text class="mono micro" x="1136" y="108" text-anchor="end">SYNC / {x(format_local(data.get('generated_at'), tz, '%Y.%m.%d  %H:%M'))} {x(timezone_label)}</text>

  <line x1="64" y1="141" x2="1136" y2="141" stroke="{BORDER}" />
  <line x1="64" y1="141" x2="132" y2="141" stroke="{ICE}" opacity="0.8" />
  <line x1="132" y1="141" x2="184" y2="141" stroke="{SAGE}" opacity="0.7" />
  <line x1="184" y1="141" x2="220" y2="141" stroke="{SAND}" opacity="0.65" />
  <text class="mono cap" x="64" y="179" style="fill:{ICE}">ACTIVITY SIGNAL</text>
  <text class="mono micro" x="1136" y="179" text-anchor="end" style="fill:{SAND}">{commits:02d} COMMITS / 7D</text>

  <line x1="64" y1="{BASELINE}" x2="1136" y2="{BASELINE}" stroke="#1D1D1D" />
  <path d="{signal_path}" fill="none" stroke="#242424" stroke-width="3" stroke-linejoin="miter" />
  <path d="{signal_path}" fill="none" stroke="url(#signalColor)" stroke-width="1.8" stroke-linejoin="miter"
        stroke-dasharray="17 12" opacity="0.92">
    <animate attributeName="stroke-dashoffset" values="580;0;-580" dur="13s" repeatCount="indefinite" />
  </path>
  <circle r="3.2" fill="{ICE}">
    <animateMotion path="{signal_path}" dur="8s" repeatCount="indefinite" />
    <animate attributeName="opacity" values="0.25;1;0.25" dur="1.6s" repeatCount="indefinite" />
  </circle>
  {''.join(day_markers)}

  <line x1="64" y1="142" x2="64" y2="558" stroke="{ACCENT}" opacity="0.07">
    <animate attributeName="x1" values="64;1136;64" dur="14s" repeatCount="indefinite" />
    <animate attributeName="x2" values="64;1136;64" dur="14s" repeatCount="indefinite" />
  </line>

  <text class="mono cap" x="64" y="329">NODE STATE</text>
  <rect x="64" y="346" width="7" height="7" fill="{state_color}">
    <animate attributeName="opacity" values="0.28;1;0.28" dur="2.4s" repeatCount="indefinite" />
  </rect>
  <text class="mono" x="86" y="371" fill="{TEXT}" font-size="34" letter-spacing="3">{x(state)}</text>
  <text class="mono cap" x="1136" y="329" text-anchor="end">LAST SIGNAL</text>
  <text class="mono" x="1136" y="371" fill="{TEXT}" font-size="18" letter-spacing="1.5" text-anchor="end">{x(relative_time(latest_at, now))}</text>

  <line x1="64" y1="412" x2="1136" y2="412" stroke="{BORDER}" />
  <text class="mono cap" x="64" y="449">LAST PUSH</text>
  <text class="mono" x="64" y="488" fill="{TEXT}" font-size="22">{x(repository)}</text>
  <text class="mono body" x="390" y="488">/ {x(branch)}</text>
  <text class="mono body" x="64" y="526">{x(message)}</text>
  <text class="mono" x="1136" y="488" fill="{TEXT}" font-size="14" text-anchor="end">{x(pushed_at)} {x(timezone_label)}</text>
  <text class="mono micro" x="1136" y="526" text-anchor="end">{x(pushed_ago)}</text>

  <line x1="64" y1="558" x2="1136" y2="558" stroke="{BORDER}" />
  <line x1="64" y1="583" x2="1136" y2="583" stroke="url(#pipelineColor)" />
  <rect x="60" y="579" width="8" height="8" fill="{ICE}"><animate attributeName="opacity" values="0.3;1;0.3" dur="2.8s" repeatCount="indefinite" /></rect>
  <rect x="412" y="579" width="8" height="8" fill="{SAGE}"><animate attributeName="opacity" values="0.3;1;0.3" dur="2.8s" begin="0.7s" repeatCount="indefinite" /></rect>
  <rect x="772" y="579" width="8" height="8" fill="{SAND}"><animate attributeName="opacity" values="0.3;1;0.3" dur="2.8s" begin="1.4s" repeatCount="indefinite" /></rect>
  <rect x="1132" y="579" width="8" height="8" fill="{ICE}"><animate attributeName="opacity" values="0.3;1;0.3" dur="2.8s" begin="2.1s" repeatCount="indefinite" /></rect>
  <rect x="0" y="579" width="8" height="8" fill="{TEXT}" opacity="0.9">
    <animate attributeName="x" values="64;1132" dur="5.6s" repeatCount="indefinite" />
    <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.06;0.94;1" dur="5.6s" repeatCount="indefinite" />
  </rect>
  <text class="mono micro" x="64" y="620" style="fill:{ICE}">CODE</text>
  <text class="mono micro" x="416" y="620" text-anchor="middle" style="fill:{SAGE}">COMMIT</text>
  <text class="mono micro" x="776" y="620" text-anchor="middle" style="fill:{SAND}">PUSH</text>
  <text class="mono micro" x="1136" y="620" text-anchor="end" style="fill:{ICE}">BUILD</text>
</svg>"""
    write_svg(ASSET_DIR / "telemetry.svg", svg)


if __name__ == "__main__":
    main()
