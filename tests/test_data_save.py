"""Data save tests: processed CSV without index, deterministic."""

from __future__ import annotations

from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pytest

from src.data import process, save


def _processed() -> pd.DataFrame:
    raw = pd.DataFrame(
        [
            [1, "1996-03-11", 4, 5, 30, 33, 41, 52],
            [2, "1996-03-18", 1, 2, 3, 4, 5, 60],
        ],
        columns=[
            "concurso",
            "data",
            "dezena_1",
            "dezena_2",
            "dezena_3",
            "dezena_4",
            "dezena_5",
            "dezena_6",
        ],
    )
    return process.process_concursos(raw)


def test_save_processed_csv_without_index(tmp_path: Path) -> None:
    # Arrange.
    df = _processed()
    target = tmp_path / "processed.csv"
    # Act.
    saved = save.save_processed(df, target)
    # Assert: file exists, header has no index column, one row per concurso.
    assert saved == target
    text = target.read_text(encoding="utf-8")
    header = text.splitlines()[0]
    assert "Unnamed" not in header
    assert header.split(",")[0] == "concurso"
    reloaded = pd.read_csv(target)
    assert len(reloaded) == 2
    assert list(reloaded["concurso"]) == [1, 2]
    assert "soma" in reloaded.columns


def test_save_rejects_empty(tmp_path: Path) -> None:
    # Arrange: empty frame.
    empty = pd.DataFrame()
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(vazio|empty)"):
        save.save_processed(empty, tmp_path / "out.csv")


def test_save_is_deterministic(tmp_path: Path) -> None:
    # Arrange.
    df = _processed()
    # Act: save twice (second overwrites).
    save.save_processed(df, tmp_path / "a.csv")
    first_bytes = (tmp_path / "a.csv").read_bytes()
    save.save_processed(df, tmp_path / "a.csv")
    second_bytes = (tmp_path / "a.csv").read_bytes()
    # Assert: identical bytes (overwrite, deterministic).
    assert first_bytes == second_bytes


def test_save_creates_parent_dirs(tmp_path: Path) -> None:
    # Arrange: nested target whose parents do not exist.
    df = _processed()
    target = tmp_path / "nested" / "dir" / "processed.csv"
    assert not target.parent.exists()
    # Act.
    save.save_processed(df, target)
    # Assert.
    assert target.is_file()


def test_save_rejects_duplicate_concurso(tmp_path: Path) -> None:
    # Arrange: processed frame with the same concurso twice.
    df = _processed()
    dup = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    assert len(dup) == len(df) + 1
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(duplicad|concurso)"):
        save.save_processed(dup, tmp_path / "dup.csv")


def test_save_accepts_str_path(tmp_path: Path) -> None:
    # Arrange.
    df = _processed()
    target = tmp_path / "processed.csv"
    # Act: str path instead of Path.
    saved = save.save_processed(df, str(target))
    # Assert.
    assert saved == target
    assert target.is_file()


def test_save_roundtrip_preserves_content(tmp_path: Path) -> None:
    # Arrange.
    df = _processed()
    target = tmp_path / "processed.csv"
    # Act.
    save.save_processed(df, target)
    reloaded = pd.read_csv(target)
    # Assert: same rows/columns, no index column, features kept.
    assert list(reloaded.columns) == list(df.columns)
    assert list(reloaded["concurso"]) == [1, 2]
    assert list(reloaded["soma"]) == list(df["soma"])
    assert "Unnamed" not in ",".join(reloaded.columns)


def test_save_overwrites_existing_file(tmp_path: Path) -> None:
    # Arrange: a file already exists with different content.
    target = tmp_path / "processed.csv"
    target.write_text("stale,content\n1,2\n", encoding="utf-8")
    df = _processed()
    # Act: overwrite with the processed frame.
    save.save_processed(df, target)
    reloaded = pd.read_csv(target)
    # Assert: stale content gone, processed content present.
    assert list(reloaded["concurso"]) == [1, 2]
    assert "soma" in reloaded.columns


def test_save_rejects_missing_concurso_column(tmp_path: Path) -> None:
    # Arrange: processed frame without the concurso column.
    df = _processed().drop(columns=["concurso"])
    # Act / Assert: explanatory error requiring one row per concurso.
    with pytest.raises(ValueError, match=r"(?i)(concurso|coluna|column|ausente)"):
        save.save_processed(df, tmp_path / "out.csv")
