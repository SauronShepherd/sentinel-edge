from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import repository_hygiene


def test_hygiene_policy_names_secrets_and_mutable_state() -> None:
    assert ".env" in repository_hygiene.SECRET_NAMES
    assert "sentinel.db" in repository_hygiene.MUTABLE_NAMES


def test_source_package_is_not_duplicated_in_allowed_source_tree() -> None:
    roots = [p.parent for p in ROOT.joinpath("src").rglob("__init__.py") if p.parent.name == "sentinel_edge"]
    assert len(roots) == 1
