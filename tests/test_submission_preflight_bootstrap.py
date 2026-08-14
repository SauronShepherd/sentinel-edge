from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_submission_preflight_bootstraps_src_before_project_import() -> None:
    source = (ROOT / "scripts/submission_preflight.py").read_text(encoding="utf-8")
    bootstrap = source.index('sys.path.insert(0, str(SRC))')
    project_import = source.index('from sentinel_edge.release.submission import')
    assert bootstrap < project_import
    assert 'REQUIRED_LOCAL_COMMANDS' in source
    assert '"setup"' not in source  # command order remains centralized in release.submission


def test_submission_preflight_verifier_is_direct_checkout_runnable() -> None:
    source = (ROOT / "scripts/verify_submission_preflight.py").read_text(encoding="utf-8")
    assert 'ROOT = Path(__file__).resolve().parents[1]' in source
    assert 'sys.path.insert(0, str(SRC))' in source
    assert source.index('sys.path.insert(0, str(SRC))') < source.index('from sentinel_edge.release.submission import')
