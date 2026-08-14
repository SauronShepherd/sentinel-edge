from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_judge_package.py"


def _module():
    spec = importlib.util.spec_from_file_location("build_judge_package_test_module", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_judge_package_local_verification_uses_isolated_venv_and_checkout_guard() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "venv.EnvBuilder" in source
    assert "system_site_packages=True" in source
    assert "verify_checkout_import" in source
    assert 'receipts["checkout_import"]' in source
    assert "smoke_python" in source


def test_checkout_import_guard_accepts_the_active_repository() -> None:
    module = _module()
    result = module.verify_checkout_import(Path(__import__("sys").executable), ROOT)
    assert result["valid"] is True, result
    assert Path(str(result["observed"])).resolve().is_relative_to((ROOT / "src").resolve())
