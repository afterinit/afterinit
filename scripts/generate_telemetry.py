"""Render a flat, line-drawn LOOLC identity with live GitHub metadata."""

from __future__ import annotations

import hashlib
import re

from render_utils import (
    ASSET_DIR,
    DATA_PATH,
    ROOT,
    STATUS_PATH,
    clip,
    now_from,
    read_json,
    relative_time,
    write_svg,
    x,
)


WIDTH = 1200
HEIGHT = 620

CANVAS = "#F2EFE7"
INK = "#171715"
MUTED = "#777166"
HAIRLINE = "#CEC8BC"
CORAL = "#F05032"
BLUE = "#3155C6"


def update_readme_cache_key(svg: str) -> None:
    """Version the README image URL using the exact generated file bytes."""
    readme = ROOT / "README.md"
    source = readme.read_text(encoding="utf-8")
    cache_key = hashlib.sha256(svg.encode("utf-8")).hexdigest()[:12]
    pattern = re.compile(r'(\./assets/telemetry\.svg)(?:\?v=[^"]+)?')
    updated, count = pattern.subn(
        lambda match: f"{match.group(1)}?v={cache_key}", source
    )
    if count == 0:
        raise RuntimeError("README telemetry image reference was not found")
    if updated != source:
        readme.write_text(updated, encoding="utf-8", newline="\n")


def render(data: dict, status: dict) -> str:
    now = now_from(data)
    push = data.get("latest_push") or {}
    repository = clip(push.get("repo"), 24, "quiet mode")
    branch = clip(push.get("branch"), 12, "—")
    pushed_ago = relative_time(push.get("timestamp"), now).lower()
    username = clip(data.get("username"), 24, "afterinit")
    domain = clip(status.get("domain"), 40, "loolc.com")
    domain_name, separator, domain_suffix = domain.partition(".")
    domain_tail = f"{separator}{domain_suffix}" if separator else ""
    tagline = clip(status.get("tagline"), 72, "Ideas, drawn into systems.")

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">{x(domain)} — a line-drawn identity for {x(username)}</title>
  <desc id="desc">A two-dimensional custom LOOLC wordmark on a warm paper background. Its statement is Let Our Originality Lead Creation. Latest public push: {x(repository)} on {x(branch)}, {x(pushed_ago)}.</desc>
  <defs>
    <pattern id="paper-grid" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M32 0H0V32" fill="none" stroke="#AFA89B" stroke-width="0.5" opacity="0.13" />
    </pattern>
    <style>
      .sans {{ font-family: Arial, Helvetica, sans-serif; }}
      .mono {{ font-family: Consolas, 'Liberation Mono', monospace; }}
      .outline {{ fill: none; stroke: {INK}; stroke-width: 3; stroke-linecap: square; stroke-linejoin: miter; }}
      .fine {{ fill: none; stroke: {MUTED}; stroke-width: 1.2; }}
      .guide {{ fill: none; stroke: {HAIRLINE}; stroke-width: 1; }}
      .label {{ fill: {INK}; font-size: 10px; font-weight: 700; letter-spacing: 1.8px; }}
      .meta {{ fill: {MUTED}; font-size: 10px; letter-spacing: 0.65px; }}
      .domain {{ fill: {INK}; font-size: 22px; font-weight: 700; letter-spacing: -0.6px; }}
      .locate-scan {{ animation: locate-scan 5.6s ease-in-out infinite; }}
      .locate-pulse {{ animation: locate-pulse 4.2s ease-out infinite; transform-origin: 97px 164px; }}
      .orbit-dot {{ animation: orbit 12s linear infinite; transform-origin: 355px 286px; }}
      .organize-ring {{ animation: organize-spin 24s linear infinite; transform-origin: 600px 286px; }}
      .organize-ring-reverse {{ animation: organize-spin-reverse 16s linear infinite; transform-origin: 600px 286px; }}
      .origin {{ animation: pulse 3.8s ease-in-out infinite; }}
      .link-signal {{ animation: link-signal 5.2s linear infinite; }}
      .link-source-pulse {{ animation: link-pulse 4.2s ease-out infinite; transform-origin: 783px 184px; }}
      .link-target-pulse {{ animation: link-pulse 4.2s ease-out -2.1s infinite; transform-origin: 894px 389px; }}
      .create-trace {{ animation: create-trace 8s linear infinite; }}
      .create-tip {{ animation: create-tip 4s ease-in-out infinite; transform-origin: 1130px 207px; }}
      .create-end-pulse {{ animation: create-end-pulse 4s ease-out infinite; transform-origin: 1114px 365px; }}
      .create-spark {{ animation: create-spark 14s linear infinite; transform-origin: 1025px 286px; }}
      .create-core {{ animation: create-core 3.4s ease-in-out infinite; transform-origin: 1025px 286px; }}
      @keyframes locate-scan {{
        0%, 12% {{ opacity: 0; transform: translateY(0); }}
        24%, 74% {{ opacity: 0.72; }}
        88%, 100% {{ opacity: 0; transform: translateY(158px); }}
      }}
      @keyframes locate-pulse {{
        0% {{ opacity: 0.55; transform: scale(0.55); }}
        70%, 100% {{ opacity: 0; transform: scale(1.65); }}
      }}
      @keyframes orbit {{ to {{ transform: rotate(360deg); }} }}
      @keyframes organize-spin {{
        from {{ transform: rotate(-28deg); }}
        to {{ transform: rotate(332deg); }}
      }}
      @keyframes organize-spin-reverse {{ to {{ transform: rotate(-360deg); }} }}
      @keyframes pulse {{
        0%, 100% {{ opacity: 0.35; transform: scale(0.78); transform-origin: 600px 286px; }}
        50% {{ opacity: 1; transform: scale(1); transform-origin: 600px 286px; }}
      }}
      @keyframes link-signal {{ to {{ stroke-dashoffset: -64; }} }}
      @keyframes link-pulse {{
        0% {{ opacity: 0.55; transform: scale(0.45); }}
        72%, 100% {{ opacity: 0; transform: scale(1.75); }}
      }}
      @keyframes create-trace {{ to {{ stroke-dashoffset: -802; }} }}
      @keyframes create-tip {{
        0%, 100% {{ opacity: 0.78; transform: scale(0.96); }}
        50% {{ opacity: 1; transform: scale(1.04); }}
      }}
      @keyframes create-end-pulse {{
        0% {{ opacity: 0.52; transform: scale(0.55); }}
        72%, 100% {{ opacity: 0; transform: scale(1.7); }}
      }}
      @keyframes create-spark {{ to {{ transform: rotate(360deg); }} }}
      @keyframes create-core {{
        0%, 100% {{ opacity: 0.55; transform: scale(0.78); }}
        50% {{ opacity: 1; transform: scale(1.08); }}
      }}
      @media (prefers-reduced-motion: reduce) {{
        .locate-scan, .locate-pulse, .orbit-dot, .organize-ring, .organize-ring-reverse,
        .origin, .link-signal, .link-source-pulse, .link-target-pulse, .create-trace,
        .create-tip, .create-end-pulse, .create-spark, .create-core {{ animation: none; }}
        .locate-scan, .locate-pulse, .link-source-pulse, .link-target-pulse,
        .create-end-pulse {{ opacity: 0; }}
        .link-signal, .create-trace {{ stroke-dashoffset: 0; opacity: 0.7; }}
      }}
    </style>
  </defs>

  <rect width="{WIDTH}" height="{HEIGHT}" fill="{CANVAS}" />
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#paper-grid)" />

  <text class="sans domain" x="58" y="61">{x(domain_name)}<tspan fill="{CORAL}">{x(domain_tail)}</tspan></text>

  <!-- A compact index carries the five ideas into the header without adding copy. -->
  <g id="header-sequence" aria-label="LOOLC visual index">
    <line x1="334" y1="53" x2="1142" y2="53" stroke="{HAIRLINE}" />

    <g aria-label="Locate symbol">
      <line x1="370" y1="34" x2="370" y2="72" stroke="{MUTED}" stroke-width="1" />
      <line x1="361" y1="41" x2="370" y2="41" stroke="{MUTED}" stroke-width="1" />
      <line x1="364" y1="65" x2="370" y2="65" stroke="{MUTED}" stroke-width="1" />
      <circle cx="370" cy="53" r="5" fill="{CORAL}" />
    </g>

    <g aria-label="Observe symbol">
      <ellipse cx="555" cy="53" rx="28" ry="10" transform="rotate(-16 555 53)" fill="none" stroke="{MUTED}" stroke-width="1" />
      <circle cx="582" cy="45" r="4" fill="{CORAL}" />
    </g>

    <g aria-label="Organize symbol">
      <circle cx="750" cy="53" r="15" fill="{CANVAS}" stroke="{INK}" stroke-width="1.2" />
      <line x1="731" y1="53" x2="769" y2="53" stroke="{MUTED}" stroke-width="1" />
      <line x1="750" y1="34" x2="750" y2="72" stroke="{MUTED}" stroke-width="1" />
      <circle cx="750" cy="53" r="5" fill="{BLUE}" />
    </g>

    <g aria-label="Link symbol">
      <path d="M922 65L943 45L964 60M943 45L959 32" fill="none" stroke="{INK}" stroke-width="1.2" />
      <circle cx="922" cy="65" r="4" fill="{CORAL}" />
      <circle cx="943" cy="45" r="5" fill="{BLUE}" />
      <circle cx="964" cy="60" r="4" fill="{CORAL}" />
    </g>

    <g aria-label="Create symbol">
      <path d="M1122 37A20 20 0 1 0 1122 69" fill="none" stroke="{INK}" stroke-width="1.2" />
      <path d="M1120 32L1136 37L1122 46Z" fill="{CORAL}" />
      <path d="M1124 38C1140 45 1140 61 1124 68" fill="none" stroke="{BLUE}" stroke-width="1" stroke-dasharray="3 5" />
    </g>
  </g>

  <line x1="58" y1="108" x2="1142" y2="108" stroke="{INK}" stroke-width="1" />
  <line x1="58" y1="112" x2="266" y2="112" stroke="{CORAL}" stroke-width="3" />

  <g id="loolc-linework">
    <!-- L / LOCATE: a measured stroke finds the idea's starting point. -->
    <g aria-label="L — locate">
      <path class="outline" d="M68 164H126V352H230V410H68Z" />
      <line class="fine" x1="52" y1="194" x2="68" y2="194" />
      <line class="fine" x1="58" y1="224" x2="68" y2="224" />
      <line class="fine" x1="52" y1="254" x2="68" y2="254" />
      <line class="fine" x1="58" y1="284" x2="68" y2="284" />
      <line class="fine" x1="52" y1="314" x2="68" y2="314" />
      <line class="fine" x1="58" y1="344" x2="68" y2="344" />
      <line class="locate-scan" x1="77" y1="190" x2="117" y2="190" stroke="{BLUE}" stroke-width="2" opacity="0" />
      <circle cx="97" cy="164" r="8" fill="{CORAL}" />
      <circle class="locate-pulse" cx="97" cy="164" r="13" fill="none" stroke="{CORAL}" stroke-width="1.2" />
      <line x1="97" y1="146" x2="97" y2="182" stroke="{CORAL}" stroke-width="1" />
      <text class="mono label" x="149" y="448" text-anchor="middle">LOCATE</text>
    </g>

    <!-- O / OBSERVE: a moving point studies the form from every angle. -->
    <g aria-label="O — observe">
      <circle class="outline" cx="355" cy="286" r="122" />
      <circle class="outline" cx="355" cy="286" r="67" />
      <ellipse class="fine" cx="355" cy="286" rx="145" ry="45" transform="rotate(-18 355 286)" />
      <g class="orbit-dot">
        <circle cx="494" cy="244" r="8" fill="{CORAL}" />
        <circle cx="494" cy="244" r="13" fill="none" stroke="{CORAL}" stroke-width="1" opacity="0.45" />
      </g>
      <text class="mono label" x="355" y="448" text-anchor="middle">OBSERVE</text>
    </g>

    <!-- O / ORGANIZE: axes and a structured ring order the information. -->
    <g aria-label="O — organize">
      <circle class="outline organize-ring" cx="600" cy="286" r="122" stroke-dasharray="492 18" />
      <circle class="outline organize-ring-reverse" cx="600" cy="286" r="67" stroke-dasharray="15 9" />
      <line class="fine" x1="557" y1="286" x2="643" y2="286" />
      <line class="fine" x1="600" y1="243" x2="600" y2="329" />
      <path d="M681 195L600 286L526 372" fill="none" stroke="{BLUE}" stroke-width="1.5" />
      <circle class="origin" cx="600" cy="286" r="9" fill="{BLUE}" />
      <circle cx="600" cy="286" r="18" fill="none" stroke="{BLUE}" stroke-width="1" opacity="0.35" />
      <text class="mono label" x="600" y="448" text-anchor="middle">ORGANIZE</text>
    </g>

    <!-- L / LINK: one continuous signal travels from source to destination. -->
    <g aria-label="L — link">
      <path class="outline" d="M762 164V410H914" />
      <path class="outline" d="M804 164V368H914" />
      <line class="outline" x1="762" y1="164" x2="804" y2="164" />
      <line class="outline" x1="914" y1="368" x2="914" y2="410" />
      <path d="M783 184V389H894" fill="none" stroke="{MUTED}" stroke-width="1.2" opacity="0.45" />
      <path class="link-signal" d="M783 184V389H894" fill="none" stroke="{BLUE}" stroke-width="2" stroke-linecap="square" stroke-linejoin="miter" stroke-dasharray="8 12" />
      <circle cx="783" cy="184" r="6" fill="{CORAL}" />
      <circle class="link-source-pulse" cx="783" cy="184" r="12" fill="none" stroke="{CORAL}" stroke-width="1.2" />
      <circle cx="894" cy="389" r="6" fill="{BLUE}" />
      <circle class="link-target-pulse" cx="894" cy="389" r="12" fill="none" stroke="{BLUE}" stroke-width="1.2" />
      <text class="mono label" x="829" y="448" text-anchor="middle">LINK</text>
    </g>

    <!-- C / CREATE: a restrained tracer stays on the letter's original open form. -->
    <g aria-label="C — create">
      <path class="outline" d="M1114 207A116 116 0 1 0 1114 365" />
      <path class="outline" d="M1075 245A64 64 0 1 0 1075 327" />
      <line class="outline" x1="1114" y1="207" x2="1075" y2="245" />
      <line class="outline" x1="1114" y1="365" x2="1075" y2="327" />
      <path class="create-trace" d="M1114 207A116 116 0 1 0 1114 365" fill="none" stroke="{CORAL}" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="28 774" />
      <path class="create-tip" d="M1122 193L1145 207L1118 216Z" fill="{CORAL}" />
      <circle cx="1114" cy="365" r="6" fill="{CORAL}" />
      <circle class="create-end-pulse" cx="1114" cy="365" r="12" fill="none" stroke="{CORAL}" stroke-width="1.2" />
      <g class="create-spark" aria-label="creation spark">
        <line x1="1025" y1="258" x2="1025" y2="272" stroke="{BLUE}" stroke-width="1.5" />
        <line x1="1025" y1="300" x2="1025" y2="314" stroke="{CORAL}" stroke-width="1.5" />
        <line x1="997" y1="286" x2="1011" y2="286" stroke="{CORAL}" stroke-width="1.5" />
        <line x1="1039" y1="286" x2="1053" y2="286" stroke="{BLUE}" stroke-width="1.5" />
        <line x1="1007" y1="268" x2="1016" y2="277" stroke="{MUTED}" stroke-width="1" />
        <line x1="1034" y1="295" x2="1043" y2="304" stroke="{MUTED}" stroke-width="1" />
      </g>
      <path class="create-core" d="M1025 274L1029 282L1037 286L1029 290L1025 298L1021 290L1013 286L1021 282Z" fill="none" stroke="{CORAL}" stroke-width="1.8" stroke-linejoin="round" />
      <circle cx="1025" cy="286" r="3.5" fill="{BLUE}" />
      <text class="mono label" x="1030" y="448" text-anchor="middle">CREATE</text>
    </g>
  </g>

  <line x1="58" y1="480" x2="1142" y2="480" stroke="{HAIRLINE}" />
  <text class="sans" x="58" y="526" fill="{INK}" font-size="28" font-weight="400" letter-spacing="-0.7">{x(tagline)}</text>

  <line x1="58" y1="554" x2="1142" y2="554" stroke="{INK}" stroke-width="1" />
  <text class="mono meta" x="58" y="584">{x(username)}</text>
  <text class="mono meta" x="1142" y="584" text-anchor="end">2026</text>
</svg>"""
    return svg.strip() + "\n"


def main() -> None:
    svg = render(read_json(DATA_PATH), read_json(STATUS_PATH))
    write_svg(ASSET_DIR / "telemetry.svg", svg)
    update_readme_cache_key(svg)


if __name__ == "__main__":
    main()
