import re
from pathlib import Path


def test_product_contract_has_743_unique_requirements() -> None:
    text = Path("docs/contracts/sentinel-edge-full-scope-product-contract-v0.22.0.md").read_text(encoding="utf-8")
    ids = re.findall(r"^\| (FR-[A-Z0-9-]+) \|", text, re.MULTILINE)
    assert len(ids) == 743
    assert len(set(ids)) == 743


def test_technical_contract_has_193_unique_adr_definitions() -> None:
    text = Path("docs/contracts/sentinel-edge-full-scope-technical-contract-v0.22.0.md").read_text(encoding="utf-8")
    ids = re.findall(r"^### (?:\d+(?:\.\d+)* )?(ADR-\d{3}) —", text, re.MULTILINE)
    assert len(ids) == 193
    assert len(set(ids)) == 193
