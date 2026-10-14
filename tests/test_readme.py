"""README tests: setup, execution and lottery-randomness disclaimer in Portuguese."""

from __future__ import annotations

from pathlib import Path

import pytest

README_PATH = Path(__file__).resolve().parents[1] / "README.md"


@pytest.fixture
def readme_text() -> str:
    return README_PATH.read_text(encoding="utf-8")


def test_readme_exists(readme_text: str) -> None:
    # Arrange: fixture already read the file.
    # Act / Assert: non-empty document.
    assert readme_text.strip() != ""


@pytest.mark.parametrize(
    "snippet",
    [
        "python3 -m venv",
        "pip install -r requirements.txt",
        "python main.py",
        "python init_project.py",
        "data/raw",
        "pytest",
    ],
)
def test_readme_documents_setup_and_execution(readme_text: str, snippet: str) -> None:
    # Arrange: full README text.
    # Act / Assert: each setup/execution snippet is documented.
    assert snippet in readme_text, f"README missing snippet: {snippet}"


@pytest.mark.parametrize(
    "snippet",
    [
        "aleat",
        "não promete",
        "educacional",
    ],
)
def test_readme_states_lottery_limitation(readme_text: str, snippet: str) -> None:
    # Arrange: full README text, lowercased for accent-tolerant matching.
    # Act / Assert: randomness disclaimer is present.
    assert snippet in readme_text.lower(), f"README missing limitation: {snippet}"


def test_readme_explains_missing_data_guidance(readme_text: str) -> None:
    # Arrange: full README text.
    # Act / Assert: points to the per-concurso CSV contract.
    assert "concurso" in readme_text
    assert "data/raw" in readme_text
