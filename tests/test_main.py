"""Entry-point tests: main runs end-to-end without real data."""

from __future__ import annotations

from pathlib import Path

import pytest

import main


@pytest.fixture
def empty_raw_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    monkeypatch.setattr("config.DATA_RAW_DIR", raw_dir)
    return raw_dir


def test_main_runs_without_real_data_reports_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    assert list(raw_dir.glob("*.csv")) == []

    monkeypatch.setattr("config.DATA_RAW_DIR", raw_dir)

    exit_code = main.main()

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "data/raw" in out
    lowered = out.lower()
    assert (
        "nenhum" in lowered
        or "missing" in lowered
        or "não" in lowered
        or "nao" in lowered
    )


def test_main_missing_data_message_is_actionable(
    empty_raw_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Arrange: empty_raw_dir fixture guarantees no CSV (asserted via filesystem).
    assert list(empty_raw_dir.glob("*.csv")) == []
    # Act.
    exit_code = main.main()
    # Assert: exit 0 plus actionable guidance in Portuguese.
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "data/raw" in out
    assert "concurso" in out
    assert ".csv" in out.lower() or "csv" in out.lower()
    assert "Caixa" in out


def test_main_is_idempotent_without_real_data(
    empty_raw_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange: no real data.
    assert list(empty_raw_dir.glob("*.csv")) == []
    # Act: run entry point twice through the highest seam.
    first = main.main()
    first_out = capsys.readouterr().out
    second = main.main()
    second_out = capsys.readouterr().out
    # Assert.
    assert first == 0
    assert second == 0
    assert first_out == second_out


def test_find_raw_files_missing_dir_returns_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange: configured raw dir does not exist.
    missing = tmp_path / "does-not-exist" / "raw"
    assert not missing.exists()
    monkeypatch.setattr("config.DATA_RAW_DIR", missing)
    # Act.
    found = main.find_raw_files()
    # Assert.
    assert found == []


def test_find_raw_files_empty_dir_returns_empty(empty_raw_dir: Path) -> None:
    # Arrange: fixture dir exists and is empty.
    # Act.
    found = main.find_raw_files()
    # Assert.
    assert found == []


def test_find_raw_files_lists_only_csv_sorted(
    empty_raw_dir: Path,
) -> None:
    # Arrange: two CSVs out of order plus a non-CSV file.
    (empty_raw_dir / "b.csv").write_text("concurso\n", encoding="utf-8")
    (empty_raw_dir / "a.csv").write_text("concurso\n", encoding="utf-8")
    (empty_raw_dir / "notes.txt").write_text("ignore me\n", encoding="utf-8")
    # Act.
    found = main.find_raw_files()
    # Assert: only CSVs, sorted.
    assert found == sorted(found)
    assert len(found) == 2
    assert found[0].endswith("a.csv")
    assert found[1].endswith("b.csv")


def test_main_with_raw_files_reports_found(
    empty_raw_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange: one realistic concurso CSV in data/raw.
    csv_path = empty_raw_dir / "concursos.csv"
    csv_path.write_text(
        "concurso,data,dezena_1,dezena_2,dezena_3,dezena_4,dezena_5,dezena_6\n"
        "1,2009-01-01,4,5,30,33,41,52\n",
        encoding="utf-8",
    )
    # Act.
    exit_code = main.main()
    # Assert.
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Encontrados 1 arquivo" in out
    assert "concursos.csv" in out
