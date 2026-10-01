from __future__ import annotations

import hashlib
import sys
import unittest
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from github_activity import build_document  # noqa: E402


class TelemetryTests(unittest.TestCase):
    def test_public_activity_is_normalized_and_profile_repo_is_excluded(self) -> None:
        raw_events = [
            {
                "id": "1",
                "type": "PushEvent",
                "created_at": "2026-09-28T02:42:16Z",
                "repo": {"name": "afterinit/afinit-blog"},
                "payload": {
                    "ref": "refs/heads/main",
                    "size": 2,
                    "commits": [
                        {"sha": "abc", "message": "fix: optimize article cache"},
                        {"sha": "def", "message": "test: cover cache refresh"},
                    ],
                },
            },
            {
                "id": "2",
                "type": "PushEvent",
                "created_at": "2026-09-28T01:00:00Z",
                "repo": {"name": "afterinit/afterinit"},
                "payload": {"ref": "refs/heads/main", "size": 1, "commits": []},
            },
        ]
        raw_repos = [
            {
                "name": "afinit-blog",
                "description": "backend",
                "language": "Java",
                "topics": ["spring-boot", "redis"],
                "pushed_at": "2026-09-28T02:42:16Z",
                "html_url": "https://github.com/afterinit/afinit-blog",
                "fork": False,
                "archived": False,
            }
        ]
        status = {"timezone": "Asia/Singapore", "exclude_repositories": ["afterinit"]}
        document = build_document(
            "afterinit",
            raw_events,
            raw_repos,
            status,
            datetime(2026, 9, 28, 3, 0, tzinfo=timezone.utc),
            "fixture",
        )

        self.assertEqual(len(document["events"]), 1)
        self.assertEqual(len(document["commits"]), 2)
        self.assertEqual(document["latest_push"]["repo"], "afinit-blog")
        self.assertEqual(document["latest_push"]["branch"], "main")
        self.assertEqual(document["stats"]["commits"], 2)
        self.assertEqual(document["stats"]["active_days"], 1)

    def test_generated_assets_are_valid_svg(self) -> None:
        for name in ("telemetry.svg",):
            path = ROOT / "assets" / name
            self.assertTrue(path.exists(), name)
            root = ET.parse(path).getroot()
            self.assertTrue(root.tag.endswith("svg"), name)

    def test_readme_uses_content_cache_key(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        match = re.search(r"\./assets/telemetry\.svg\?v=([0-9a-f]{12})", readme)
        self.assertIsNotNone(match)
        # Git may check out LF files as CRLF on Windows; hash canonical SVG text.
        svg = (ROOT / "assets" / "telemetry.svg").read_text(encoding="utf-8").encode("utf-8")
        self.assertEqual(match.group(1), hashlib.sha256(svg).hexdigest()[:12])


if __name__ == "__main__":
    unittest.main()
