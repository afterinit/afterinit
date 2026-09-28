"""Render the recent public commit timeline."""

from __future__ import annotations

from render_utils import (
    ACCENT,
    ASSET_DIR,
    BORDER,
    DATA_PATH,
    DIM,
    STATUS_PATH,
    TEXT,
    base_svg,
    clip,
    format_local,
    line,
    now_from,
    read_json,
    relative_time,
    text,
    timezone_from,
    write_svg,
)


def main() -> None:
    data = read_json(DATA_PATH)
    status = read_json(STATUS_PATH)
    commits = data.get("commits") or []
    now = now_from(data)
    tz = timezone_from(status)

    body: list[str] = []
    body.append(text(48, 43, "DEVELOPMENT TIMELINE", "label"))
    body.append(text(1152, 43, "RECENT PUBLIC PUSH COMMITS", "micro", text_anchor="end"))
    body.append(line(48, 65, 1152, 65))
    body.append(text(48, 101, "NOW", "label"))
    body.append(line(82, 116, 82, 379, BORDER))

    if commits:
        for index, commit in enumerate(commits[:5]):
            y_pos = 139 + index * 52
            body.append(f'<rect x="77" y="{y_pos - 7}" width="10" height="10" fill="{ACCENT if index == 0 else DIM}" />')
            body.append(text(111, y_pos, relative_time(commit.get("timestamp"), now), "micro"))
            body.append(text(231, y_pos, clip(commit.get("repo"), 28), "value"))
            body.append(text(515, y_pos, f"/{clip(commit.get('branch'), 22)}", "soft"))
            body.append(text(1152, y_pos, format_local(commit.get("timestamp"), tz, "%m-%d %H:%M"), "micro", text_anchor="end"))
            body.append(text(231, y_pos + 22, clip(commit.get("message"), 91), "soft"))
    else:
        body.append(f'<rect x="77" y="132" width="10" height="10" fill="{DIM}" />')
        body.append(text(111, 141, "NO SIGNAL", "micro"))
        body.append(text(231, 141, "AWAITING FIRST PUBLIC PUSH", "value"))
        body.append(text(231, 166, "THE NEXT WORKFLOW RUN WILL POPULATE THIS TIMELINE", "soft"))

    body.append(text(48, 405, "COMMIT TIME / PUBLIC REPOSITORY HISTORY     BRANCH / LATEST PUSH SIGNAL", "micro"))
    svg = base_svg(1200, 425, "\n  ".join(body), title="Recent development timeline")
    write_svg(ASSET_DIR / "timeline.svg", svg)


if __name__ == "__main__":
    main()
