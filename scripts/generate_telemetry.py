"""Render an animated compute core driven by public GitHub activity."""

from __future__ import annotations

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

INK = "#030407"
TEXT = "#F3F2F0"
MUTED = "#8B8C96"
BORDER = "#292D37"
CYAN = "#78AEB8"
BLUE = "#7185B5"
VIOLET = "#907CAD"
ROSE = "#A67D8B"
GOLD = "#AA936E"
MINT = "#7F998E"
SLATE = "#66717E"


def normalized_days(raw_days: object) -> list[dict]:
    days = raw_days[-7:] if isinstance(raw_days, list) else []
    return ([{"day": "--", "commits": 0}] * (7 - len(days))) + days


def activity_bars(days: list[dict]) -> str:
    values = [max(0, int(day.get("commits") or 0)) for day in days]
    maximum = max(values, default=0)
    colors = (CYAN, BLUE, VIOLET, ROSE, GOLD, MINT, CYAN)
    parts: list[str] = []
    for index, (day, value) in enumerate(zip(days, values)):
        x_pos = 62 + index * 65
        height = 5 if value == 0 or maximum == 0 else 18 + round((value / maximum) * 66)
        y_pos = 390 - height
        color = colors[index] if value else SLATE
        parts.append(
            f'<line x1="{x_pos + 12}" y1="306" x2="{x_pos + 12}" y2="390" '
            f'stroke="#171A21" />'
            f'<rect x="{x_pos}" y="{y_pos}" width="24" height="{height}" fill="{color}" '
            f'opacity="{0.78 if value else 0.20}">'
            f'<animate attributeName="opacity" values="{0.45 if value else 0.12};'
            f'{0.92 if value else 0.30};{0.45 if value else 0.12}" dur="4.2s" '
            f'begin="{index * 0.28:.2f}s" repeatCount="indefinite" /></rect>'
            f'<rect x="{x_pos}" y="{y_pos - 4}" width="24" height="1" fill="{color}" opacity="0.9" />'
            f'<text class="mono micro" x="{x_pos + 12}" y="411" text-anchor="middle" '
            f'style="fill:{color}">{x(day.get("day", "--"))}</text>'
            f'<text class="mono nano" x="{x_pos + 12}" y="428" text-anchor="middle">{value:02d}</text>'
        )
    return "".join(parts)


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
        "ACTIVE": MINT,
        "IDLE": GOLD,
        "OFFLINE": SLATE,
        "NO SIGNAL": DIM,
    }.get(state, DIM)
    commits = int(stats.get("commits") or 0)
    pushes = int(stats.get("pushes") or 0)
    days = normalized_days(stats.get("daily"))
    bars = activity_bars(days)

    if push:
        repository = clip(push.get("repo"), 32)
        branch = clip(push.get("branch"), 20)
        message = clip(push.get("message"), 67)
        pushed_at = format_local(push.get("timestamp"), tz, "%Y.%m.%d  /  %H:%M:%S")
        pushed_ago = relative_time(push.get("timestamp"), now)
    else:
        repository = "AWAITING FIRST PUBLIC PUSH"
        branch = "—"
        message = "RUN THE TELEMETRY WORKFLOW TO ESTABLISH SIGNAL"
        pushed_at = "—"
        pushed_ago = "NO SIGNAL"

    project = clip(status.get("project"), 28)
    tagline = clip(status.get("tagline"), 58)
    synced_at = format_local(data.get("generated_at"), tz, "%Y.%m.%d  %H:%M")
    orbit_dash = max(9, min(25, 28 - commits))

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">afterinit activity core</title>
  <desc id="desc">An animated developer compute core generated from recent public GitHub activity.</desc>
  <defs>
    <linearGradient id="surface" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#05080C" />
      <stop offset="0.48" stop-color="{INK}" />
      <stop offset="1" stop-color="#0A060A" />
    </linearGradient>
    <linearGradient id="spectrum" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{CYAN}" />
      <stop offset="0.28" stop-color="{BLUE}" />
      <stop offset="0.55" stop-color="{VIOLET}" />
      <stop offset="0.78" stop-color="{ROSE}" />
      <stop offset="1" stop-color="{GOLD}" />
    </linearGradient>
    <linearGradient id="coreTop" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{CYAN}" stop-opacity="0.72" />
      <stop offset="0.48" stop-color="{BLUE}" stop-opacity="0.54" />
      <stop offset="1" stop-color="{VIOLET}" stop-opacity="0.68" />
    </linearGradient>
    <linearGradient id="coreLeft" x1="0" y1="0" x2="0.8" y2="1">
      <stop offset="0" stop-color="#263652" />
      <stop offset="1" stop-color="#10141D" />
    </linearGradient>
    <linearGradient id="coreRight" x1="0" y1="0" x2="0.8" y2="1">
      <stop offset="0" stop-color="#3B2943" />
      <stop offset="1" stop-color="#151018" />
    </linearGradient>
    <radialGradient id="aura" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="{VIOLET}" stop-opacity="0.26" />
      <stop offset="0.42" stop-color="{BLUE}" stop-opacity="0.13" />
      <stop offset="1" stop-color="{CYAN}" stop-opacity="0" />
    </radialGradient>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#171A22" stroke-width="1" opacity="0.48" />
    </pattern>
    <filter id="glow" x="-120%" y="-120%" width="340%" height="340%">
      <feGaussianBlur stdDeviation="6" result="blur" />
      <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
    </filter>
    <filter id="softGlow" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur stdDeviation="18" />
    </filter>
    <style>
      .mono {{ font-family: 'IBM Plex Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', monospace; }}
      .cap {{ fill: {MUTED}; font-size: 11px; letter-spacing: 2.5px; }}
      .micro {{ fill: #6F717C; font-size: 10px; letter-spacing: 1.35px; }}
      .nano {{ fill: #4F515A; font-size: 8px; letter-spacing: 1px; }}
      .body {{ fill: #A5A4AA; font-size: 13px; }}
      .cursor {{ animation: blink 1.2s steps(1, end) infinite; }}
      @keyframes blink {{ 0%, 46% {{ opacity: 1; }} 47%, 100% {{ opacity: 0; }} }}
      @media (prefers-reduced-motion: reduce) {{ .cursor {{ animation: none; }} }}
    </style>
  </defs>

  <rect x="0.5" y="0.5" width="1199" height="719" fill="url(#surface)" stroke="{BORDER}" />
  <rect x="1" y="1" width="1198" height="718" fill="url(#grid)" opacity="0.30" />
  <ellipse cx="855" cy="286" rx="370" ry="285" fill="url(#aura)" opacity="0.82" />
  <ellipse cx="855" cy="286" rx="145" ry="105" fill="{VIOLET}" opacity="0.06" filter="url(#softGlow)">
    <animate attributeName="opacity" values="0.035;0.12;0.035" dur="6s" repeatCount="indefinite" />
  </ellipse>

  <path d="M 18 48 V 18 H 48 M 1152 18 H 1182 V 48 M 18 672 V 702 H 48 M 1152 702 H 1182 V 672"
        fill="none" stroke="#343844" />
  <path d="M 560 80 L 1118 570 M 650 64 L 1140 488 M 620 560 L 1112 112"
        fill="none" stroke="#171A23" opacity="0.62" />
  <text class="mono nano" x="24" y="360" transform="rotate(-90 24 360)">DEV NODE / TELEMETRY CHANNEL 01</text>

  <!-- Identity / information plane -->
  <text class="mono micro" x="60" y="46" style="fill:{CYAN}">SYS / AFTERINIT.01</text>
  <text class="mono" x="60" y="103" fill="{TEXT}" font-size="55" font-weight="700" letter-spacing="7">AFTERINIT<tspan class="cursor" fill="{CYAN}">_</tspan></text>
  <text class="mono cap" x="62" y="138">{x(status.get('role', 'JAVA BACKEND / COMPUTER SCIENCE'))}</text>
  <text class="mono body" x="62" y="169">{x(tagline)}</text>
  <rect x="62" y="190" width="38" height="2" fill="{CYAN}" />
  <rect x="108" y="190" width="26" height="2" fill="{BLUE}" />
  <rect x="142" y="190" width="18" height="2" fill="{VIOLET}" />
  <rect x="168" y="190" width="12" height="2" fill="{ROSE}" />

  <line x1="60" y1="215" x2="515" y2="215" stroke="{BORDER}" />
  <text class="mono micro" x="60" y="239">NODE STATE</text>
  <rect x="60" y="253" width="7" height="7" fill="{state_color}" filter="url(#glow)">
    <animate attributeName="opacity" values="0.3;1;0.3" dur="2.5s" repeatCount="indefinite" />
  </rect>
  <text class="mono" x="78" y="268" fill="{TEXT}" font-size="20" letter-spacing="2">{x(state)}</text>
  <line x1="213" y1="230" x2="213" y2="274" stroke="{BORDER}" />
  <text class="mono micro" x="238" y="239">LAST SIGNAL</text>
  <text class="mono" x="238" y="268" fill="{TEXT}" font-size="15">{x(relative_time(latest_at, now))}</text>
  <line x1="397" y1="230" x2="397" y2="274" stroke="{BORDER}" />
  <text class="mono micro" x="423" y="239">ACTIVITY</text>
  <text class="mono" x="423" y="268" fill="{TEXT}" font-size="15">{commits:02d}C / {pushes:02d}P</text>

  <text class="mono cap" x="60" y="303" style="fill:{CYAN}">ACTIVITY SPECTRUM / 7D</text>
  <line x1="60" y1="390" x2="515" y2="390" stroke="#242832" />
  {bars}

  <line x1="60" y1="452" x2="515" y2="452" stroke="{BORDER}" />
  <text class="mono cap" x="60" y="480">LAST PUSH</text>
  <text class="mono" x="60" y="518" fill="{TEXT}" font-size="21">{x(repository)}</text>
  <text class="mono body" x="380" y="518">/ {x(branch)}</text>
  <text class="mono body" x="60" y="552">{x(message)}</text>
  <text class="mono micro" x="60" y="582">{x(pushed_at)} {x(timezone_label)}</text>
  <text class="mono micro" x="515" y="582" text-anchor="end" style="fill:{GOLD}">{x(pushed_ago)}</text>

  <!-- Animated compute core -->
  <text class="mono cap" x="635" y="63" style="fill:{VIOLET}">COMPUTE CORE / ACTIVITY DRIVEN</text>
  <text class="mono micro" x="1138" y="63" text-anchor="end">SYNC / {x(synced_at)} {x(timezone_label)}</text>
  <path d="M 625 82 H 720 M 1050 82 H 1140 V 172 M 625 485 V 555 H 715 M 1050 555 H 1140 V 465"
        fill="none" stroke="#303440" />

  <!-- Circuit traces -->
  <g fill="none" stroke-width="1">
    <path d="M 647 151 H 708 L 774 216" stroke="{CYAN}" stroke-dasharray="5 9" opacity="0.62">
      <animate attributeName="stroke-dashoffset" values="56;0" dur="5s" repeatCount="indefinite" />
    </path>
    <path d="M 1086 167 H 1024 L 930 230" stroke="{ROSE}" stroke-dasharray="5 9" opacity="0.58">
      <animate attributeName="stroke-dashoffset" values="0;56" dur="5.8s" repeatCount="indefinite" />
    </path>
    <path d="M 642 433 H 715 L 785 357" stroke="{MINT}" stroke-dasharray="5 9" opacity="0.55">
      <animate attributeName="stroke-dashoffset" values="48;0" dur="6.2s" repeatCount="indefinite" />
    </path>
    <path d="M 1088 432 H 1015 L 920 362" stroke="{GOLD}" stroke-dasharray="5 9" opacity="0.60">
      <animate attributeName="stroke-dashoffset" values="0;48" dur="5.4s" repeatCount="indefinite" />
    </path>
  </g>
  <g class="mono nano">
    <rect x="639" y="143" width="16" height="16" fill="none" stroke="{CYAN}" />
    <text x="662" y="155" style="fill:{CYAN}">API</text>
    <rect x="1078" y="159" width="16" height="16" fill="none" stroke="{ROSE}" />
    <text x="1070" y="187" text-anchor="end" style="fill:{ROSE}">PUSH</text>
    <rect x="634" y="425" width="16" height="16" fill="none" stroke="{MINT}" />
    <text x="658" y="438" style="fill:{MINT}">CODE</text>
    <rect x="1080" y="424" width="16" height="16" fill="none" stroke="{GOLD}" />
    <text x="1070" y="438" text-anchor="end" style="fill:{GOLD}">BUILD</text>
  </g>

  <!-- Counter-rotating orbital system -->
  <g transform="rotate(-14 855 286)">
    <ellipse cx="855" cy="286" rx="250" ry="108" fill="none" stroke="url(#spectrum)"
             stroke-width="1.2" stroke-dasharray="{orbit_dash} 14" opacity="0.62">
      <animateTransform attributeName="transform" type="rotate" from="0 855 286" to="360 855 286" dur="34s" repeatCount="indefinite" />
    </ellipse>
    <circle cx="605" cy="286" r="4" fill="{CYAN}" filter="url(#glow)">
      <animateMotion path="M 605 286 A 250 108 0 1 1 1105 286 A 250 108 0 1 1 605 286" dur="10s" repeatCount="indefinite" />
    </circle>
  </g>
  <g transform="rotate(18 855 286)">
    <ellipse cx="855" cy="286" rx="198" ry="82" fill="none" stroke="url(#spectrum)"
             stroke-width="1" stroke-dasharray="3 12" opacity="0.48">
      <animateTransform attributeName="transform" type="rotate" from="360 855 286" to="0 855 286" dur="24s" repeatCount="indefinite" />
    </ellipse>
    <circle cx="657" cy="286" r="3.5" fill="{ROSE}" filter="url(#glow)">
      <animateMotion path="M 657 286 A 198 82 0 1 0 1053 286 A 198 82 0 1 0 657 286" dur="7.5s" repeatCount="indefinite" />
    </circle>
  </g>

  <!-- Isometric core -->
  <polygon points="855,190 963,251 855,312 747,251" fill="none" stroke="url(#spectrum)" opacity="0.34" />
  <polygon points="855,205 947,257 855,309 763,257" fill="url(#coreTop)" stroke="url(#spectrum)" stroke-width="1.3" />
  <polygon points="763,257 855,309 855,391 763,339" fill="url(#coreLeft)" stroke="{BLUE}" stroke-opacity="0.55" />
  <polygon points="947,257 855,309 855,391 947,339" fill="url(#coreRight)" stroke="{ROSE}" stroke-opacity="0.55" />
  <path d="M 855 309 V 391 M 763 257 L 855 309 L 947 257" fill="none" stroke="#B7A9C2" opacity="0.28" />
  <path d="M 784 327 L 836 357 M 874 358 L 925 329" fill="none" stroke="url(#spectrum)" stroke-dasharray="5 7" opacity="0.64">
    <animate attributeName="stroke-dashoffset" values="48;0" dur="5s" repeatCount="indefinite" />
  </path>

  <g>
    <polygon points="855,225 908,256 855,287 802,256" fill="url(#spectrum)" opacity="0.52" filter="url(#glow)">
      <animate attributeName="opacity" values="0.28;0.76;0.28" dur="4s" repeatCount="indefinite" />
    </polygon>
    <polygon points="855,235 891,256 855,277 819,256" fill="#090B12" stroke="{TEXT}" stroke-opacity="0.55"
             stroke-dasharray="6 5">
      <animate attributeName="stroke-dashoffset" values="44;0" dur="5.5s" repeatCount="indefinite" />
      <animateTransform attributeName="transform" type="rotate" from="0 855 256" to="360 855 256" dur="28s" repeatCount="indefinite" />
    </polygon>
    <rect x="850" y="251" width="10" height="10" fill="{TEXT}" filter="url(#glow)">
      <animate attributeName="opacity" values="0.35;1;0.35" dur="1.8s" repeatCount="indefinite" />
    </rect>
  </g>

  <!-- Moving circuit packets -->
  <circle cx="647" cy="151" r="2.8" fill="{CYAN}" filter="url(#glow)">
    <animateMotion path="M 647 151 H 708 L 807 250" dur="4.8s" repeatCount="indefinite" />
  </circle>
  <circle cx="1088" cy="432" r="2.8" fill="{GOLD}" filter="url(#glow)">
    <animateMotion path="M 1088 432 H 1015 L 904 348" dur="5.2s" begin="-1.7s" repeatCount="indefinite" />
  </circle>

  <text class="mono micro" x="855" y="469" text-anchor="middle">CURRENT PROCESS</text>
  <text class="mono" x="855" y="496" text-anchor="middle" fill="{TEXT}" font-size="16" letter-spacing="1.8">{x(project)}</text>
  <text class="mono nano" x="855" y="519" text-anchor="middle" style="fill:{VIOLET}">SIGNAL / {commits:02d} COMMITS / {pushes:02d} PUSHES</text>

  <!-- System data rail -->
  <line x1="60" y1="626" x2="1140" y2="626" stroke="url(#spectrum)" opacity="0.58" />
  <g>
    <rect x="56" y="622" width="8" height="8" fill="{CYAN}" />
    <rect x="413" y="622" width="8" height="8" fill="{BLUE}" />
    <rect x="773" y="622" width="8" height="8" fill="{VIOLET}" />
    <rect x="1136" y="622" width="8" height="8" fill="{GOLD}" />
    <circle cx="60" cy="626" r="4" fill="{TEXT}" filter="url(#glow)">
      <animate attributeName="cx" values="60;1140" dur="5.8s" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.06;0.94;1" dur="5.8s" repeatCount="indefinite" />
    </circle>
  </g>
  <text class="mono micro" x="60" y="656" style="fill:{CYAN}">CODE</text>
  <text class="mono micro" x="417" y="656" text-anchor="middle" style="fill:{BLUE}">COMMIT</text>
  <text class="mono micro" x="777" y="656" text-anchor="middle" style="fill:{VIOLET}">PUSH</text>
  <text class="mono micro" x="1140" y="656" text-anchor="end" style="fill:{GOLD}">BUILD</text>
  <text class="mono nano" x="60" y="690">PUBLIC GITHUB TELEMETRY / ACTIVITY STATE IS NOT LIVE PRESENCE</text>
  <text class="mono nano" x="1140" y="690" text-anchor="end">AUTO SYNC / 06H</text>

  <!-- Slow glass scan -->
  <rect x="0" y="1" width="1" height="718" fill="{CYAN}" opacity="0.06">
    <animate attributeName="x" values="1;1198;1" dur="18s" repeatCount="indefinite" />
  </rect>
</svg>"""
    write_svg(ASSET_DIR / "telemetry.svg", svg)


if __name__ == "__main__":
    main()
