"""Skeleton init tests: required directories exist after idempotent init."""

from __future__ import annotations

from pathlib import Path

import pytest

import init_project

REQUIRED_REL_DIRS = [
    "data/raw",
    "data/processed",
    "data/outputs",
    "notebooks",
    "src/data",
    "src/models",
    "tests",
    "models",
]


def test_ensure_directories_creates_required_structure(tmp_path: Path) -> None:
    created = init_project.ensure_directories(tmp_path)

    expected = [
        "data/raw",
        "data/processed",
        "data/outputs",
        "notebooks",
        "src/data",
        "src/models",
        "tests",
        "models",
    ]
    for rel in expected:
        assert (tmp_path / rel).is_dir(), f"missing directory: {rel}"
    assert len(created) == len(expected)


def test_ensure_directories_is_idempotent(tmp_path: Path) -> None:
    init_project.ensure_directories(tmp_path)
    created_again = init_project.ensure_directories(tmp_path)

    for path in created_again:
        assert path.is_dir()


@pytest.mark.parametrize("rel", REQUIRED_REL_DIRS)
def test_ensure_directories_creates_each_required_dir(tmp_path: Path, rel: str) -> None:
    # Arrange: fresh isolated root.
    # Act.
    init_project.ensure_directories(tmp_path)
    # Assert: each contract directory exists.
    assert (tmp_path / rel).is_dir(), f"missing directory: {rel}"


def test_ensure_directories_preserves_existing_files(tmp_path: Path) -> None:
    # Arrange: sentinel file inside a required dir.
    sentinel = tmp_path / "data" / "raw" / "sentinel.csv"
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.write_text("concurso,data\n1,2009-01-01\n", encoding="utf-8")
    # Act: run init twice (idempotence must never delete).
    init_project.ensure_directories(tmp_path)
    init_project.ensure_directories(tmp_path)
    # Assert.
    assert sentinel.is_file()
    assert sentinel.read_text(encoding="utf-8").startswith("concurso")


def test_ensure_directories_creates_missing_base_dir(tmp_path: Path) -> None:
    # Arrange: base dir does not exist yet.
    base_dir = tmp_path / "newroot" / "nested"
    assert not base_dir.exists()
    # Act.
    created = init_project.ensure_directories(base_dir)
    # Assert.
    assert base_dir.is_dir()
    assert len(created) == len(REQUIRED_REL_DIRS)
    for path in created:
        assert path.is_dir()
