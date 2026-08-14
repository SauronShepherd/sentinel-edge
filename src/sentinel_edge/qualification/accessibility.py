"""Deterministic static checks for the core local UI accessibility contract."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AccessibilityAudit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    passed: bool
    checks: tuple[str, ...]
    failures: tuple[str, ...]


def audit_core_ui_accessibility(html: str, javascript: str) -> AccessibilityAudit:
    checks = {
        "keyboard_focus": ":focus-visible" in html and "tabindex" in html,
        "text_alternative": "aria-labelledby" in html and "aria-live" in html,
        "zoom_reflow": "@media" in html and "max-width" in html,
        "contrast_boundary": "border:" in html and "color" in html,
        "tabular_equivalent": "<table>" in javascript and "<caption>" in javascript,
        "pause_or_control": "Resume live projection" in html and "type=\"button\"" in html,
        "no_color_only_state": "State:</strong>" in javascript and "Coverage:</strong>" in javascript,
    }
    failures = tuple(sorted(name for name, passed in checks.items() if not passed))
    return AccessibilityAudit(passed=not failures, checks=tuple(sorted(checks)), failures=failures)
