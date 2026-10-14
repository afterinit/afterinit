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
      .orbit-dot {{ animation: orbit 12s linear infinite; transform-origin: 355px 286px; }}
      .origin {{ animation: pulse 3.8s ease-in-out infinite; }}
      .continuation {{ animation: travel 8s linear infinite; }}
      @keyframes orbit {{ to {{ transform: rotate(360deg); }} }}
      @keyframes pulse {{
        0%, 100% {{ opacity: 0.35; transform: scale(0.78); transform-origin: 600px 286px; }}
        50% {{ opacity: 1; transform: scale(1); transform-origin: 600px 286px; }}
      }}
      @keyframes travel {{ to {{ stroke-dashoffset: -48; }} }}
      @media (prefers-reduced-motion: reduce) {{
        .orbit-dot, .origin, .continuation {{ animation: none; }}
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
      <circle cx="97" cy="164" r="8" fill="{CORAL}" />
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
      <circle class="outline" cx="600" cy="286" r="122" stroke-dasharray="492 18" transform="rotate(-28 600 286)" />
      <circle class="outline" cx="600" cy="286" r="67" stroke-dasharray="15 9" />
      <line class="fine" x1="557" y1="286" x2="643" y2="286" />
      <line class="fine" x1="600" y1="243" x2="600" y2="329" />
      <path d="M681 195L600 286L526 372" fill="none" stroke="{BLUE}" stroke-width="1.5" />
      <circle class="origin" cx="600" cy="286" r="9" fill="{BLUE}" />
      <circle cx="600" cy="286" r="18" fill="none" stroke="{BLUE}" stroke-width="1" opacity="0.35" />
      <text class="mono label" x="600" y="448" text-anchor="middle">ORGANIZE</text>
    </g>

    <!-- L / LINK: colored nodes meet at the letter's inner corner. -->
    <g aria-label="L — link">
      <path class="outline" d="M744 164H802V352H914V410H744Z" />
      <line x1="724" y1="140" x2="724" y2="426" stroke="{BLUE}" stroke-width="1.5" stroke-dasharray="3 8" />
      <circle cx="724" cy="410" r="6" fill="{BLUE}" />
      <path d="M802 352L844 310L877 341" fill="none" stroke="{CORAL}" stroke-width="2.5" />
      <path d="M844 310L875 286M844 310L829 279" fill="none" stroke="{BLUE}" stroke-width="1.2" />
      <circle cx="802" cy="352" r="5" fill="{CORAL}" />
      <circle cx="844" cy="310" r="7" fill="{BLUE}" />
      <circle cx="877" cy="341" r="5" fill="{CORAL}" />
      <text class="mono label" x="829" y="448" text-anchor="middle">LINK</text>
    </g>

    <!-- C / CREATE: the open letter releases its path into a new form. -->
    <g aria-label="C — create">
      <path class="outline" d="M1114 207A116 116 0 1 0 1114 365" />
      <path class="outline" d="M1075 245A64 64 0 1 0 1075 327" />
      <line class="outline" x1="1114" y1="207" x2="1075" y2="245" />
      <line class="outline" x1="1114" y1="365" x2="1075" y2="327" />
      <path class="continuation" d="M1115 208C1164 242 1164 330 1115 364" fill="none" stroke="{BLUE}" stroke-width="1.5" stroke-dasharray="4 8" />
      <path d="M1122 193L1145 207L1118 216Z" fill="{CORAL}" />
      <circle cx="1114" cy="365" r="6" fill="{CORAL}" />
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
