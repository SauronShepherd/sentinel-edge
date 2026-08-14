from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_admitted_candidate_package_command_requires_fresh_copy_verification() -> None:
    source = (ROOT / "scripts/dev.py").read_text(encoding="utf-8")
    assert 'candidate_payload.get("release_admitted") is True' in source
    assert 'package_command.append("--verify-local")' in source
    build = (ROOT / "scripts/build_judge_package.py").read_text(encoding="utf-8")
    assert "venv.EnvBuilder" in build
    assert "verify_checkout_import" in build
