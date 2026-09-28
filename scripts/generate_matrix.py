"""Render a 7 x 24 local-time activity matrix."""

from __future__ import annotations

from datetime import timedelta

from render_utils import (
    ACCENT,
    ASSET_DIR,
    BORDER,
    DATA_PATH,
    DIM,
    MUTED,
    STATUS_PATH,
    base_svg,
    line,
    now_from,
    read_json,
    text,
    write_svg,
)


def normalized_matrix(data: dict) -> list[dict]:
    supplied = (data.get("stats") or {}).get("matrix") or []
    if len(supplied) == 7 and all(len(row.get("hours") or []) == 24 for row in supplied):
        return supplied
    today = now_from(data).date()
    return [
        {
            "date": (today - timedelta(days=offset)).isoformat(),
            "day": (today - timedelta(days=offset)).strftime("%a").upper(),
            "hours": [0] * 24,
        }
        for offset in range(6, -1, -1)
    ]


def shade(value: int, maximum: int) -> tuple[str, float]:
    if value <= 0 or maximum <= 0:
        return DIM, 0.22
    ratio = value / maximum
    return ACCENT, 0.32 + ratio * 0.68


def main() -> None:
    data = read_json(DATA_PATH)
    status = read_json(STATUS_PATH)
    matrix = normalized_matrix(data)
    maximum = max((max(row["hours"], default=0) for row in matrix), default=0)
    timezone_label = status.get("timezone_label", "UTC")

    body: list[str] = []
    body.append(text(48, 43, "ACTIVITY MATRIX / 7 × 24", "label"))
    body.append(text(1152, 43, f"LOCAL TIME / {timezone_label}", "micro", text_anchor="end"))
    body.append(line(48, 65, 1152, 65))

    start_x = 194
    start_y = 105
    cell_w = 31
    gap = 5
    for hour in range(24):
        if hour % 3 == 0:
            body.append(text(start_x + hour * (cell_w + gap) + cell_w // 2, 88, f"{hour:02d}", "micro", text_anchor="middle"))

    for row_index, row in enumerate(matrix):
        y_pos = start_y + row_index * 34
        body.append(text(48, y_pos + 15, row.get("day", "---"), "label"))
        body.append(text(106, y_pos + 15, str(row.get("date", ""))[5:], "micro"))
        for hour, value in enumerate(row["hours"]):
            color, opacity = shade(int(value or 0), maximum)
            body.append(
                f'<rect x="{start_x + hour * (cell_w + gap)}" y="{y_pos}" width="{cell_w}" height="18" '
                f'fill="{color}" opacity="{opacity:.2f}" />'
            )

    body.append(line(48, 352, 1152, 352, BORDER, 0.8))
    body.append(text(48, 379, "PUBLIC PUSH COMMITS GROUPED BY PUSH HOUR", "micro"))
    body.append(text(1152, 379, "DARK / NONE     LIGHT / HIGHER ACTIVITY", "micro", text_anchor="end"))
    svg = base_svg(1200, 400, "\n  ".join(body), title="Seven by twenty-four public activity matrix")
    write_svg(ASSET_DIR / "activity-matrix.svg", svg)


if __name__ == "__main__":
    main()
