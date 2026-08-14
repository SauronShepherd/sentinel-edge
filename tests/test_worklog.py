from datetime import date
from pathlib import Path
import re


def test_post_hackathon_worklog_sections_map_to_paths_and_commands() -> None:
    text = (Path(__file__).resolve().parents[1] / "HACKATHON_WORKLOG.md").read_text(encoding="utf-8")
    sections = re.split(r"(?m)^## (\d{4}-\d{2}-\d{2})\s*$", text)
    dated = []
    for index in range(1, len(sections), 2):
        if date.fromisoformat(sections[index]) > date(2026, 6, 10):
            dated.append(sections[index + 1])
    assert dated
    for section in dated:
        assert "Changed paths:" in section
        assert "Exact verification commands:" in section
        assert re.search(r"(?:pytest|python(?:\.exe)?|\.venv)", section)
