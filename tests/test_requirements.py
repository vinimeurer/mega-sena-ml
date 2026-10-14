"""Requirements tests: pinned dependencies installable via venv."""

from __future__ import annotations

import re
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as dist_version
from pathlib import Path

import pytest

REQUIRED = [
    "pandas",
    "matplotlib",
    "seaborn",
    "scikit-learn",
    "xgboost",
    "jupyter",
    "pytest",
]

PINNED_LINE = re.compile(r"^[A-Za-z0-9_.\-]+==\d+(\.\d+)*$")


def test_requirements_pins_expected_dependencies() -> None:
    req_path = Path(__file__).resolve().parents[1] / "requirements.txt"
    assert req_path.is_file(), "requirements.txt is missing"

    lines = req_path.read_text(encoding="utf-8").splitlines()
    content_lower = "\n".join(lines).lower()
    for dep in REQUIRED:
        assert dep.lower() in content_lower, f"missing dependency: {dep}"

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        assert "==" in stripped, f"unpinned dependency line: {stripped}"


def _read_pin_lines() -> list[str]:
    req_path = Path(__file__).resolve().parents[1] / "requirements.txt"
    raw_lines = req_path.read_text(encoding="utf-8").splitlines()
    return [
        line.strip()
        for line in raw_lines
        if line.strip() and not line.strip().startswith("#")
    ]


@pytest.mark.parametrize("dep", REQUIRED)
def test_requirements_pins_each_expected_dependency(dep: str) -> None:
    # Arrange: pinned lines from requirements.txt.
    pin_lines = _read_pin_lines()
    # Act: find the pin for this dependency (case-insensitive, normalized).
    normalized = dep.lower().replace("_", "-")
    matches = [
        line
        for line in pin_lines
        if line.lower().split("==")[0].replace("_", "-") == normalized
    ]
    # Assert: exactly one pin with a non-empty version.
    assert len(matches) == 1, f"missing or duplicated pin: {dep}"
    name, pinned_version = matches[0].split("==")
    assert name.strip() != ""
    assert pinned_version.strip() != ""


@pytest.mark.parametrize(
    "line",
    [
        "pandas==2.2.3",
        "matplotlib==3.9.2",
        "seaborn==0.13.2",
        "scikit-learn==1.5.2",
        "xgboost==2.1.2",
        "jupyter==1.1.1",
        "pytest==8.3.4",
    ],
)
def test_requirements_pin_format_is_name_and_version(line: str) -> None:
    # Arrange: a known-good literal pin.
    # Act / Assert: strict format name==numeric-version.
    assert PINNED_LINE.match(line) is not None


def test_requirements_all_lines_use_strict_pin_format() -> None:
    # Arrange: every non-comment line.
    pin_lines = _read_pin_lines()
    assert pin_lines != []
    # Act / Assert.
    for line in pin_lines:
        assert PINNED_LINE.match(line) is not None, f"bad pin format: {line}"


@pytest.mark.parametrize("dep", REQUIRED)
def test_required_distributions_are_installed(dep: str) -> None:
    # Arrange: distribution name as listed in requirements.txt.
    # Act.
    try:
        installed = dist_version(dep)
    except PackageNotFoundError:
        installed = ""
    # Assert: installed with a non-empty version, no network needed.
    assert installed != "", f"distribution not installed: {dep}"
