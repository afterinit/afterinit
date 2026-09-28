"""Render the primary developer telemetry dashboard."""

from __future__ import annotations

from render_utils import (
    ACCENT,
    ASSET_DIR,
    BORDER,
    DATA_PATH,
    DIM,
    MUTED,
    STATUS_PATH,
    TEXT,
    activity_state,
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
    x,
)


def main() -> None:
    data = read_json(DATA_PATH)
    status = read_json(STATUS_PATH)
    now = now_from(data)
    tz = timezone_from(status)
    events = data.get("events", [])
    repos = data.get("repos", [])
    stats = data.get("stats", {})
    push = data.get("latest_push")
    latest_at = events[0].get("timestamp") if events else None
    state, state_color = activity_state(latest_at, now)
    timezone_label = status.get("timezone_label", "UTC")

    body: list[str] = []
    body.append(
        f'<text class="mono" x="48" y="67" fill="{TEXT}" font-size="46" font-weight="700" '
        f'letter-spacing="4">AFTERINIT<tspan class="cursor" fill="{ACCENT}">_</tspan></text>'
    )
    body.append(text(50, 99, status.get("role", "JAVA BACKEND / COMPUTER SCIENCE"), "label"))
    body.append(text(50, 122, clip(status.get("tagline"), 74), "soft"))
    body.append(text(1150, 39, "LOCAL TIME // LAST SYNC", "micro", text_anchor="end"))
    body.append(
        text(
            1150,
            64,
            format_local(data.get("generated_at"), tz, "%Y / %m / %d   %H:%M:%S") + f"  {timezone_label}",
            "value",
            text_anchor="end",
        )
    )
    body.append(f'<rect x="1088" y="91" width="9" height="9" fill="{state_color}" />')
    body.append(text(1150, 100, f"GITHUB ACTIVITY: {state}", "label", text_anchor="end"))
    body.append(line(48, 141, 1152, 141))
    body.append(line(774, 141, 774, 852, BORDER, 0.9))

    # Live public status
    body.append(text(48, 177, "01 / LIVE DEVELOPER STATUS", "label"))
    live_rows = [
        ("STATUS", state),
        ("LAST PUSH", format_local((push or {}).get("timestamp"), tz, "%Y-%m-%d %H:%M") if push else "AWAITING FIRST SYNC"),
        ("ACTIVE REPOSITORY", (push or {}).get("repo") or "—"),
        ("CURRENT BRANCH", (push or {}).get("branch") or "—"),
        ("LAST ACTIVITY", relative_time(latest_at, now)),
    ]
    for index, (label, value) in enumerate(live_rows):
        y_pos = 219 + index * 31
        body.append(text(48, y_pos, label, "micro"))
        css = "value" if label != "STATUS" else "label"
        body.append(text(244, y_pos, clip(value, 54), css, fill=state_color if label == "STATUS" else TEXT))

    # Last push
    body.append(line(48, 389, 734, 389))
    body.append(text(48, 421, "02 / LAST PUSH", "label"))
    if push:
        body.append(
            f'<text class="mono" x="48" y="466" fill="{TEXT}" font-size="28" letter-spacing="1">'
            f'{x(format_local(push.get("timestamp"), tz))}</text>'
        )
        body.append(text(48, 500, clip(push.get("repo"), 34), "value"))
        body.append(text(405, 500, f"BRANCH / {clip(push.get('branch'), 24)}", "soft"))
        body.append(text(48, 535, clip(push.get("message"), 74), "soft"))
        body.append(line(48, 555, 734, 555, BORDER, 0.7))
        body.append(text(734, 579, relative_time(push.get("timestamp"), now), "label", text_anchor="end"))
    else:
        body.append(text(48, 471, "AWAITING FIRST PUBLIC PUSH", "value"))
        body.append(text(48, 503, "RUN THE TELEMETRY WORKFLOW TO ESTABLISH SIGNAL", "micro"))

    # Activity stream
    body.append(line(48, 612, 734, 612))
    body.append(text(48, 644, "03 / ACTIVITY STREAM", "label"))
    if events:
        for index, event in enumerate(events[:5]):
            y_pos = 682 + index * 33
            timestamp = format_local(event.get("timestamp"), tz, "%m-%d %H:%M")
            target = event.get("repo") or "unknown"
            if event.get("branch"):
                target += "/" + str(event["branch"])
            body.append(text(48, y_pos, timestamp, "micro"))
            body.append(text(175, y_pos, clip(event.get("action"), 12), "label"))
            body.append(text(316, y_pos, clip(target, 46), "soft"))
    else:
        body.append(text(48, 687, "[--:--:--]  NO PUBLIC ACTIVITY LOADED", "soft"))

    # Weekly report
    right_x = 812
    body.append(text(right_x, 177, "04 / WEEKLY DEV PULSE", "label"))
    weekly = [
        ("COMMITS", stats.get("commits", 0)),
        ("PUSHES", stats.get("pushes", 0)),
        ("ACTIVE REPOS", stats.get("active_repos", 0)),
        ("ACTIVE DAYS", f"{stats.get('active_days', 0)} / 7"),
    ]
    for index, (label, value) in enumerate(weekly):
        col = index % 2
        row = index // 2
        x_pos = right_x + col * 178
        y_pos = 218 + row * 66
        body.append(text(x_pos, y_pos, label, "micro"))
        body.append(
            f'<text class="mono" x="{x_pos}" y="{y_pos + 32}" fill="{TEXT}" font-size="25">{x(value)}</text>'
        )
    body.append(text(right_x, 348, "MOST ACTIVE", "micro"))
    body.append(text(right_x + 338, 348, clip(stats.get("most_active"), 25), "value", text_anchor="end"))

    # Active repositories
    body.append(line(right_x, 377, 1152, 377))
    body.append(text(right_x, 409, "05 / ACTIVE NODES", "label"))
    if repos:
        for index, repo in enumerate(repos[:3]):
            y_pos = 451 + index * 79
            number = f"{index + 1:02d}"
            meta_parts = [repo.get("language") or "UNSPECIFIED"] + list(repo.get("topics") or [])[:2]
            meta = " / ".join(str(part) for part in meta_parts if part)
            body.append(text(right_x, y_pos, number, "micro"))
            body.append(text(right_x + 42, y_pos, clip(repo.get("name"), 28), "value"))
            body.append(text(right_x + 42, y_pos + 23, clip(meta, 43), "micro"))
            body.append(
                text(
                    1152,
                    y_pos + 23,
                    relative_time(repo.get("pushed_at"), now),
                    "micro",
                    text_anchor="end",
                )
            )
    else:
        body.append(text(right_x, 454, "NO REPOSITORY SIGNAL", "soft"))

    # User-controlled focus
    body.append(line(right_x, 664, 1152, 664))
    body.append(text(right_x, 696, "06 / CURRENT FOCUS", "label"))
    body.append(text(right_x, 733, "MODE", "micro"))
    body.append(text(1152, 733, clip(status.get("status"), 20), "value", text_anchor="end"))
    body.append(text(right_x, 766, "PROJECT", "micro"))
    body.append(text(1152, 766, clip(status.get("project"), 28), "value", text_anchor="end"))
    focus = status.get("focus") if isinstance(status.get("focus"), list) else []
    body.append(text(right_x, 803, " / ".join(clip(item, 20) for item in focus[:2]) or "—", "soft"))
    if len(focus) > 2:
        body.append(text(right_x, 827, " / ".join(clip(item, 20) for item in focus[2:4]), "soft"))

    body.append(line(48, 852, 1152, 852))
    body.append(text(48, 879, "SOURCE / PUBLIC GITHUB EVENTS API", "micro"))
    body.append(text(1152, 879, "ACTIVE ≠ LIVE PRESENCE", "micro", text_anchor="end"))

    svg = base_svg(1200, 900, "\n  ".join(body), title="afterinit developer telemetry", animated=True)
    write_svg(ASSET_DIR / "telemetry.svg", svg)


if __name__ == "__main__":
    main()
