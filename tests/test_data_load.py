"""Data load tests: canonical per-concurso raw CSV contract."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.data import load

VALID_HEADER = "concurso,data,dezena_1,dezena_2,dezena_3,dezena_4,dezena_5,dezena_6\n"
VALID_ROWS = (
    "1,1996-03-11,4,5,30,33,41,52\n"
    "2,1996-03-18,1,2,3,4,5,60\n"
    "3,1996-03-25,10,20,30,40,50,60\n"
)


def _write_csv(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_load_valid_concurso_csv(tmp_path: Path) -> None:
    # Arrange: canonical per-concurso CSV with 3 concursos.
    csv_path = _write_csv(tmp_path / "concursos.csv", VALID_HEADER + VALID_ROWS)
    # Act.
    df = load.load_raw_csv(csv_path)
    # Assert: 3 rows, required columns present, raw untouched (6 dezenas kept).
    assert len(df) == 3
    assert "concurso" in df.columns
    assert "data" in df.columns
    for col in ("dezena_1", "dezena_2", "dezena_3", "dezena_4", "dezena_5", "dezena_6"):
        assert col in df.columns


def test_load_missing_file_fails_with_clear_message(tmp_path: Path) -> None:
    # Arrange: path that does not exist.
    missing = tmp_path / "nope.csv"
    assert not missing.exists()
    # Act / Assert: clear message mentioning the missing file and data/raw.
    with pytest.raises(
        FileNotFoundError, match=r"(?i)(não|nao|missing|not found|inexistente)"
    ):
        load.load_raw_csv(missing)


def test_load_malformed_csv_fails_with_clear_message(tmp_path: Path) -> None:
    # Arrange: truncated/quoting-broken CSV.
    bad = _write_csv(tmp_path / "bad.csv", 'concurso,data,dezena_1\n1,"unclosed,2\n')
    # Act / Assert.
    with pytest.raises(
        ValueError, match=r"(?i)(malformado|malformed|parse|invalid|inválido)"
    ):
        load.load_raw_csv(bad)


def test_load_missing_columns_fails(tmp_path: Path) -> None:
    # Arrange: legacy annual shape (ano,...) without concurso/data columns.
    legacy = _write_csv(
        tmp_path / "legacy.csv",
        "ano,dezena_1,dezena_2,dezena_3,dezena_4,dezena_5,dezena_6\n2009,10,27,40,46,49,58\n",
    )
    # Act / Assert: explanatory error naming the missing columns.
    with pytest.raises(ValueError, match=r"(?i)(coluna|column|concurso)"):
        load.load_raw_csv(legacy)


def test_load_empty_csv_fails(tmp_path: Path) -> None:
    # Arrange: header only, no concurso rows.
    empty = _write_csv(tmp_path / "empty.csv", VALID_HEADER)
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(vazio|empty|sem registros|no rows)"):
        load.load_raw_csv(empty)


def test_load_zero_byte_file_fails_malformed(tmp_path: Path) -> None:
    # Arrange: 0-byte file (no header at all).
    zero = tmp_path / "zero.csv"
    zero.write_bytes(b"")
    # Act / Assert: malformed, not a silent empty frame.
    with pytest.raises(
        ValueError, match=r"(?i)(malformado|malformed|vazio|empty|inválido|invalid)"
    ):
        load.load_raw_csv(zero)


def test_load_directory_path_fails_not_found(tmp_path: Path) -> None:
    # Arrange: a directory instead of a file.
    assert tmp_path.is_dir()
    # Act / Assert: same clear FileNotFoundError as a missing file.
    with pytest.raises(
        FileNotFoundError, match=r"(?i)(não|nao|missing|not found|inexistente)"
    ):
        load.load_raw_csv(tmp_path)


def test_load_accepts_str_path(tmp_path: Path) -> None:
    # Arrange: canonical CSV addressed as str (not Path).
    csv_path = _write_csv(tmp_path / "concursos.csv", VALID_HEADER + VALID_ROWS)
    # Act.
    df = load.load_raw_csv(str(csv_path))
    # Assert.
    assert len(df) == 3


def test_load_accepts_extra_columns_keeps_rows(tmp_path: Path) -> None:
    # Arrange: canonical columns plus one extra audit column.
    extra = _write_csv(
        tmp_path / "extra.csv",
        VALID_HEADER.strip() + ",extra\n1,1996-03-11,4,5,30,33,41,52,foo\n",
    )
    # Act.
    df = load.load_raw_csv(extra)
    # Assert: required contract holds; extra column preserved, raw untouched.
    assert len(df) == 1
    for col in ("concurso", "data", "dezena_1", "dezena_6"):
        assert col in df.columns


def test_load_semicolon_separated_canonical_is_accepted(tmp_path: Path) -> None:
    # Arrange: canonical names with ';' separator (autodetected since Caixa support).
    semi = _write_csv(
        tmp_path / "semi.csv",
        "concurso;data;dezena_1;dezena_2;dezena_3;dezena_4;dezena_5;dezena_6\n"
        "1;1996-03-11;4;5;30;33;41;52\n",
    )
    # Act.
    df = load.load_raw_csv(semi)
    # Assert: separator autodetected, same contract as the comma format.
    assert len(df) == 1
    assert int(df.iloc[0]["concurso"]) == 1
    assert int(df.iloc[0]["dezena_1"]) == 4


def test_load_does_not_modify_raw_file(tmp_path: Path) -> None:
    # Arrange: canonical CSV with known bytes.
    csv_path = _write_csv(tmp_path / "concursos.csv", VALID_HEADER + VALID_ROWS)
    before = csv_path.read_bytes()
    # Act.
    load.load_raw_csv(csv_path)
    # Assert: raw file bytes identical (carga nunca altera o original).
    assert csv_path.read_bytes() == before


CAIXA_HEADER = (
    "Concurso;Data do Sorteio;Bola1;Bola2;Bola3;Bola4;Bola5;Bola6;"
    "Ganhadores 6 acertos;Cidade / UF;Rateio 6 acertos;"
    "Ganhadores 5 acertos;Rateio 5 acertos;Ganhadores 4 acertos;"
    "Rateio 4 acertos;Acumulado 6 acertos;Arrecadação Total;"
    "Estimativa prêmio;Acumulado Sorteio Especial Mega da Virada;Observação\n"
)
CAIXA_ROWS = (
    "1;11/03/1996;4;5;30;33;41;52;0;;R$0,00;17;R$39.158,92;"
    "2016;R$330,21;R$1.714.650,23;R$0,00;R$0,00;R$0,00;\n"
    "2;18/03/1996;9;37;39;41;43;49;1;PR;R$2.307.162,23;65;"
    "R$14.424,02;4488;R$208,91;R$0,00;R$0,00;R$0,00;R$0,00;\n"
    '3;25/03/1996;10;11;29;30;36;47;2;"RN; SP";R$391.192,51;62;'
    "R$10.515,93;4261;R$153,01;R$0,00;R$0,00;R$0,00;R$0,00;\n"
)


def _write_caixa_csv(path: Path) -> Path:
    path.write_bytes(b"\xef\xbb\xbf" + (CAIXA_HEADER + CAIXA_ROWS).encode("utf-8"))
    return path


def test_load_accepts_official_caixa_format_as_is(tmp_path: Path) -> None:
    # Arrange: small inline replica of the official Caixa file
    # (BOM, ';' separator, Bola1-6 + payout extras, DD/MM/YYYY).
    csv_path = _write_caixa_csv(tmp_path / "Mega-Sena.csv")
    # Act.
    df = load.load_raw_csv(csv_path)
    # Assert: canonical contract holds, extras ignored, 3 concursos.
    assert len(df) == 3
    for col in ("concurso", "data", "dezena_1", "dezena_6"):
        assert col in df.columns
    first = df.iloc[0]
    assert int(first["concurso"]) == 1
    assert str(first["data"]) == "11/03/1996"
    assert [
        int(first[c])
        for c in (
            "dezena_1",
            "dezena_2",
            "dezena_3",
            "dezena_4",
            "dezena_5",
            "dezena_6",
        )
    ] == [4, 5, 30, 33, 41, 52]


def test_load_caixa_quoted_city_with_semicolon_stays_one_row(tmp_path: Path) -> None:
    # Arrange: Caixa replica where Cidade/UF is '"RN; SP"' (quoted ';').
    csv_path = _write_caixa_csv(tmp_path / "Mega-Sena.csv")
    # Act.
    df = load.load_raw_csv(csv_path)
    # Assert: quoted separator does not split rows; concurso 3 intact.
    assert len(df) == 3
    third = df[df["concurso"] == 3].iloc[0]
    assert [
        int(third[c])
        for c in (
            "dezena_1",
            "dezena_2",
            "dezena_3",
            "dezena_4",
            "dezena_5",
            "dezena_6",
        )
    ] == [10, 11, 29, 30, 36, 47]


def test_load_caixa_result_is_processable(tmp_path: Path) -> None:
    # Arrange: Caixa replica loaded as-is.
    from src.data import process as process_mod

    csv_path = _write_caixa_csv(tmp_path / "Mega-Sena.csv")
    df = load.load_raw_csv(csv_path)
    # Act.
    out = process_mod.process_concursos(df)
    # Assert: one row per concurso, known-good soma for concurso 1 (4+5+30+33+41+52).
    assert len(out) == 3
    assert int(out[out["concurso"] == 1].iloc[0]["soma"]) == 165
