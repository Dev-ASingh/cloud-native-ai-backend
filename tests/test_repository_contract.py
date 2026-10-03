from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_design_contract_documents_exist() -> None:
    required = (
        "README.md",
        "docs/architecture.md",
        "docs/threat-model.md",
        "docs/api-contract.md",
        "docs/test-strategy.md",
    )

    missing = [path for path in required if not (ROOT / path).is_file()]

    assert not missing, f"Missing design contract files: {missing}"
