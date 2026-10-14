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
    empty_raw_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange: one realistic concurso CSV in data/raw; isolate processed output.
    csv_path = empty_raw_dir / "concursos.csv"
    csv_path.write_text(
        "concurso,data,dezena_1,dezena_2,dezena_3,dezena_4,dezena_5,dezena_6\n"
        "1,2009-01-01,4,5,30,33,41,52\n",
        encoding="utf-8",
    )
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("config.DATA_PROCESSED_DIR", processed_dir)
    # Act.
    exit_code = main.main()
    # Assert.
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Encontrados 1 arquivo" in out
    assert "concursos.csv" in out


def test_main_with_invalid_dezenas_reports_clear_error(
    empty_raw_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange: CSV with dezena 61 (out of 1-60); isolate processed output.
    (empty_raw_dir / "bad.csv").write_text(
        "concurso,data,dezena_1,dezena_2,dezena_3,dezena_4,dezena_5,dezena_6\n"
        "1,2009-01-01,4,5,30,33,41,61\n",
        encoding="utf-8",
    )
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("config.DATA_PROCESSED_DIR", processed_dir)
    # Act.
    exit_code = main.main()
    # Assert: non-zero exit with explanatory message pointing to data/raw.
    assert exit_code != 0
    out = capsys.readouterr().out
    assert "data/raw" in out
    assert "Erro" in out or "erro" in out.lower()


def test_main_with_unusable_csv_reports_no_usable_file(
    empty_raw_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange: legacy annual shape (no concurso column), not usable.
    (empty_raw_dir / "legacy.csv").write_text(
        "ano,dezena_1,dezena_2,dezena_3,dezena_4,dezena_5,dezena_6\n"
        "2009,10,27,40,46,49,58\n",
        encoding="utf-8",
    )
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("config.DATA_PROCESSED_DIR", processed_dir)
    # Act.
    exit_code = main.main()
    # Assert.
    assert exit_code != 0
    out = capsys.readouterr().out
    assert "Nenhum CSV utilizável" in out or "data/raw" in out


def test_main_exit_code_is_2_on_unusable_csv(
    empty_raw_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange: CSV presente mas inutilizável (dezena 61 fora de 1-60).
    (empty_raw_dir / "bad.csv").write_text(
        "concurso,data,dezena_1,dezena_2,dezena_3,dezena_4,dezena_5,dezena_6\n"
        "1,2009-01-01,4,5,30,33,41,61\n",
        encoding="utf-8",
    )
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("config.DATA_PROCESSED_DIR", processed_dir)
    # Act.
    exit_code = main.main()
    # Assert: contrato do ticket/nota — CSV inutilizável sai com exit 2.
    assert exit_code == 2
    out = capsys.readouterr().out
    assert "data/raw" in out


def test_process_first_usable_skips_broken_file(
    empty_raw_dir: Path,
) -> None:
    # Arrange: a.csv quebrado (sem colunas canônicas), b.csv válido.
    (empty_raw_dir / "a.csv").write_text(
        "ano,dezena_1\n2009,10\n",
        encoding="utf-8",
    )
    (empty_raw_dir / "b.csv").write_text(
        "concurso,data,dezena_1,dezena_2,dezena_3,dezena_4,dezena_5,dezena_6\n"
        "1,2009-01-01,4,5,30,33,41,52\n",
        encoding="utf-8",
    )
    raw_files = main.find_raw_files()
    assert [Path(p).name for p in raw_files] == ["a.csv", "b.csv"]
    # Act.
    source, processed = main.process_first_usable(raw_files)
    # Assert: primeiro utilizável em ordem alfabética (b.csv).
    assert source.endswith("b.csv")
    assert len(processed) == 1
    assert int(processed.iloc[0]["soma"]) == 165


def test_process_first_usable_prefers_alphabetical_first(
    empty_raw_dir: Path,
) -> None:
    # Arrange: two valid CSVs with different concursos.
    (empty_raw_dir / "b.csv").write_text(
        "concurso,data,dezena_1,dezena_2,dezena_3,dezena_4,dezena_5,dezena_6\n"
        "2,2009-01-02,1,2,3,4,5,60\n",
        encoding="utf-8",
    )
    (empty_raw_dir / "a.csv").write_text(
        "concurso,data,dezena_1,dezena_2,dezena_3,dezena_4,dezena_5,dezena_6\n"
        "1,2009-01-01,4,5,30,33,41,52\n",
        encoding="utf-8",
    )
    # Act.
    source, processed = main.process_first_usable(main.find_raw_files())
    # Assert: usa o primeiro em ordem alfabética.
    assert source.endswith("a.csv")
    assert list(processed["concurso"]) == [1]


def test_process_first_usable_all_unusable_raises(empty_raw_dir: Path) -> None:
    # Arrange: only a legacy file, nothing usable.
    (empty_raw_dir / "legacy.csv").write_text(
        "ano,dezena_1\n2009,10\n",
        encoding="utf-8",
    )
    # Act / Assert: erro explicativo apontando para data/raw.
    with pytest.raises(ValueError, match=r"(?i)(data/raw|utilizável|utilizavel)"):
        main.process_first_usable(main.find_raw_files())


def test_main_saves_processed_csv_without_index(
    empty_raw_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange: one valid concurso CSV; isolate processed output.
    (empty_raw_dir / "concursos.csv").write_text(
        "concurso,data,dezena_1,dezena_2,dezena_3,dezena_4,dezena_5,dezena_6\n"
        "1,2009-01-01,4,5,30,33,41,52\n"
        "2,2009-01-08,1,2,3,4,5,60\n",
        encoding="utf-8",
    )
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("config.DATA_PROCESSED_DIR", processed_dir)
    # Act.
    assert main.main() == 0
    # Assert: processado salvo sem coluna de índice, um registro por concurso.
    import pandas as pd  # type: ignore[import-untyped]

    target = processed_dir / main.PROCESSED_FILENAME
    assert target.is_file()
    text = target.read_text(encoding="utf-8")
    assert "Unnamed" not in text.splitlines()[0]
    reloaded = pd.read_csv(target)
    assert list(reloaded["concurso"]) == [1, 2]
    assert "soma" in reloaded.columns
    assert "n_pares" in reloaded.columns


def test_run_pipeline_deterministic_bytes(
    empty_raw_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange: valid CSV; isolate processed output.
    csv_path = empty_raw_dir / "concursos.csv"
    csv_path.write_text(
        "concurso,data,dezena_1,dezena_2,dezena_3,dezena_4,dezena_5,dezena_6\n"
        "1,2009-01-01,4,5,30,33,41,52\n"
        "2,2009-01-08,1,2,3,4,5,60\n",
        encoding="utf-8",
    )
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("config.DATA_PROCESSED_DIR", processed_dir)
    # Act: run twice, then rewrite raw rows shuffled and run again.
    _, target, _ = main.run_pipeline()
    first_bytes = target.read_bytes()
    _, target, _ = main.run_pipeline()
    second_bytes = target.read_bytes()
    csv_path.write_text(
        "concurso,data,dezena_1,dezena_2,dezena_3,dezena_4,dezena_5,dezena_6\n"
        "2,2009-01-08,60,5,4,3,2,1\n"
        "1,2009-01-01,52,33,5,4,41,30\n",
        encoding="utf-8",
    )
    _, target, _ = main.run_pipeline()
    shuffled_bytes = target.read_bytes()
    # Assert: reprocessar os mesmos dados gera bytes idênticos.
    assert first_bytes == second_bytes
    assert first_bytes == shuffled_bytes


def test_main_with_caixa_format_processes_as_is(
    empty_raw_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange: official Caixa file as-is (BOM, ';', Bola1-6 + payout extras).
    (empty_raw_dir / "Mega-Sena.csv").write_bytes(
        b"\xef\xbb\xbf"
        + (
            b"Concurso;Data do Sorteio;Bola1;Bola2;Bola3;Bola4;Bola5;Bola6;"
            b"Ganhadores 6 acertos;Cidade / UF;Rateio 6 acertos\n"
            b"1;11/03/1996;4;5;30;33;41;52;0;;R$0,00\n"
            b"2;18/03/1996;9;37;39;41;43;49;1;PR;R$2.307.162,23\n"
        )
    )
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("config.DATA_PROCESSED_DIR", processed_dir)
    # Act: run through the highest seam (entry point).
    exit_code = main.main()
    # Assert: exit 0, processed CSV saved without index, known-good soma.
    assert exit_code == 0
    capsys.readouterr()
    import pandas as pd  # type: ignore[import-untyped]

    target = processed_dir / main.PROCESSED_FILENAME
    assert target.is_file()
    text = target.read_text(encoding="utf-8")
    assert "Unnamed" not in text.splitlines()[0]
    reloaded = pd.read_csv(target)
    assert list(reloaded["concurso"]) == [1, 2]
    assert int(reloaded[reloaded["concurso"] == 1].iloc[0]["soma"]) == 165
