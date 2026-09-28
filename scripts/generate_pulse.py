"""Render a monochrome seven-day commit signal."""

from __future__ import annotations

from datetime import timedelta

from render_utils import (
    ACCENT,
    ASSET_DIR,
    BORDER,
    DATA_PATH,
    DIM,
    MUTED,
    TEXT,
    base_svg,
    bounded_signal,
    line,
    now_from,
    read_json,
    text,
    write_svg,
)


def normalized_days(data: dict) -> list[dict]:
    supplied = (data.get("stats") or {}).get("daily") or []
    if len(supplied) == 7:
        return supplied
    today = now_from(data).date()
    return [
        {
            "date": (today - timedelta(days=offset)).isoformat(),
            "day": (today - timedelta(days=offset)).strftime("%a").upper(),
            "commits": 0,
            "pushes": 0,
        }
        for offset in range(6, -1, -1)
    ]


def main() -> None:
    data = read_json(DATA_PATH)
    stats = data.get("stats") or {}
    daily = normalized_days(data)
    maximum = max((int(day.get("commits") or 0) for day in daily), default=0)
    cells = 24

    body: list[str] = []
    body.append(text(48, 43, "CODE PULSE / LAST 7 DAYS", "label"))
    body.append(text(1152, 43, f"{stats.get('commits', 0)} COMMITS  /  {stats.get('pushes', 0)} PUSHES", "micro", text_anchor="end"))
    body.append(line(48, 65, 1152, 65))

    for row, day in enumerate(daily):
        y_pos = 96 + row * 34
        commits = int(day.get("commits") or 0)
        pushes = int(day.get("pushes") or 0)
        filled = bounded_signal(commits, maximum, cells)
        body.append(text(48, y_pos + 12, day.get("day", "---"), "label"))
        body.append(text(112, y_pos + 12, str(day.get("date", ""))[5:], "micro"))
        for index in range(cells):
            color = ACCENT if index < filled else DIM
            opacity = 0.28 + (index / max(1, cells - 1)) * 0.62 if index < filled else 0.24
            body.append(
                f'<rect x="{224 + index * 31}" y="{y_pos}" width="23" height="12" '
                f'fill="{color}" opacity="{opacity:.2f}" />'
            )
        body.append(text(1000, y_pos + 12, f"{commits:02d} COMMIT{'S' if commits != 1 else ''}", "micro"))
        body.append(text(1152, y_pos + 12, f"{pushes:02d} PUSH{'ES' if pushes != 1 else ''}", "micro", text_anchor="end"))

    body.append(line(48, 336, 1152, 336, BORDER, 0.8))
    body.append(text(48, 354, "SIGNAL AMPLITUDE NORMALIZED TO THE BUSIEST DAY", "micro"))
    body.append(text(1152, 354, "PUBLIC PUSH COMMITS", "micro", text_anchor="end"))
    svg = base_svg(1200, 370, "\n  ".join(body), title="Seven-day code pulse")
    write_svg(ASSET_DIR / "pulse.svg", svg)


if __name__ == "__main__":
    main()

