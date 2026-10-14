"""Data process tests: jogo validation and per-concurso features."""

from __future__ import annotations

import pandas as pd  # type: ignore[import-untyped]
import pytest

from src.data import process

HEADER = [
    "concurso",
    "data",
    "dezena_1",
    "dezena_2",
    "dezena_3",
    "dezena_4",
    "dezena_5",
    "dezena_6",
]


def _valid_history() -> pd.DataFrame:
    return pd.DataFrame(
        [
            [1, "1996-03-11", 4, 5, 30, 33, 41, 52],
            [2, "1996-03-18", 1, 2, 3, 4, 5, 60],
            [3, "1996-03-25", 10, 20, 30, 40, 50, 60],
        ],
        columns=HEADER,
    )


def test_process_valid_history_derives_features() -> None:
    # Arrange: 3 valid concursos.
    raw = _valid_history()
    # Act.
    out = process.process_concursos(raw)
    # Assert: one row per concurso, known-good literals (not recomputed).
    assert len(out) == 3
    assert list(out["concurso"]) == [1, 2, 3]
    row1 = out[out["concurso"] == 1].iloc[0]
    assert int(row1["soma"]) == 165
    assert int(row1["n_pares"]) == 3
    assert int(row1["n_impares"]) == 3
    row2 = out[out["concurso"] == 2].iloc[0]
    assert int(row2["soma"]) == 75
    assert int(row2["n_pares"]) == 3
    assert int(row2["n_impares"]) == 3
    row3 = out[out["concurso"] == 3].iloc[0]
    assert int(row3["soma"]) == 210
    assert int(row3["n_pares"]) == 6
    assert int(row3["n_impares"]) == 0


def test_process_edge_dezenas_1_and_60() -> None:
    # Arrange: jogo on the limits 1 and 60.
    raw = pd.DataFrame(
        [[9, "1996-05-01", 1, 2, 3, 4, 5, 60]],
        columns=HEADER,
    )
    # Act.
    out = process.process_concursos(raw)
    # Assert: accepted, soma literal 1+2+3+4+5+60=75.
    assert len(out) == 1
    assert int(out.iloc[0]["soma"]) == 75


def test_process_rejects_out_of_range() -> None:
    # Arrange: dezena 0 below 1.
    raw = pd.DataFrame(
        [[1, "1996-03-11", 0, 5, 30, 33, 41, 52]],
        columns=HEADER,
    )
    # Act / Assert: explanatory error with range 1-60.
    with pytest.raises(ValueError, match=r"(?i)(1.*60|intervalo|range|fora)"):
        process.process_concursos(raw)


def test_process_rejects_dezena_above_60() -> None:
    # Arrange: dezena 61 above 60.
    raw = pd.DataFrame(
        [[1, "1996-03-11", 4, 5, 30, 33, 41, 61]],
        columns=HEADER,
    )
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(1.*60|intervalo|range|fora)"):
        process.process_concursos(raw)


def test_process_rejects_duplicates_in_jogo() -> None:
    # Arrange: repeated dezena 5 in the same jogo.
    raw = pd.DataFrame(
        [[1, "1996-03-11", 5, 5, 30, 33, 41, 52]],
        columns=HEADER,
    )
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(repetid|duplicat)"):
        process.process_concursos(raw)


def test_process_rejects_missing_dezena() -> None:
    # Arrange: one dezena ausente (NaN => jogo com menos de 6 dezenas válidas).
    raw = pd.DataFrame(
        [[1, "1996-03-11", 4, 5, None, 33, 41, 52]],
        columns=HEADER,
    )
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(6|ausente|missing|nulo|null)"):
        process.process_concursos(raw)


def test_process_rejects_empty() -> None:
    # Arrange: empty frame with canonical columns.
    raw = pd.DataFrame(columns=HEADER)
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(vazio|empty)"):
        process.process_concursos(raw)


def test_process_rejects_duplicate_concurso() -> None:
    # Arrange: same concurso number twice.
    raw = pd.DataFrame(
        [
            [1, "1996-03-11", 4, 5, 30, 33, 41, 52],
            [1, "1996-03-18", 1, 2, 3, 4, 5, 60],
        ],
        columns=HEADER,
    )
    # Act / Assert: one row per concurso required.
    with pytest.raises(ValueError, match=r"(?i)(duplicat|repetid|concurso)"):
        process.process_concursos(raw)


def test_process_is_deterministic() -> None:
    # Arrange: same concursos in different input order, dezenas unsorted.
    ordered = _valid_history()
    shuffled = pd.DataFrame(
        [
            [3, "1996-03-25", 60, 10, 50, 20, 40, 30],
            [1, "1996-03-11", 52, 4, 33, 5, 41, 30],
            [2, "1996-03-18", 60, 5, 4, 3, 2, 1],
        ],
        columns=HEADER,
    )
    # Act.
    first = process.process_concursos(ordered)
    second = process.process_concursos(shuffled)
    # Assert: same canonical output (sorted concursos, sorted dezenas).
    pd.testing.assert_frame_equal(first, second)
    pd.testing.assert_frame_equal(first, process.process_concursos(ordered))


def test_compute_frequencia_counts_appearances() -> None:
    # Arrange.
    raw = _valid_history()
    processed = process.process_concursos(raw)
    # Act.
    freq = process.compute_frequencia(processed)
    # Assert: known-good literals; 18 slots total; unseen dezena 7 is zero.
    by_dezena = dict(zip(freq["dezena"], freq["frequencia"]))
    assert by_dezena[4] == 2
    assert by_dezena[60] == 2
    assert by_dezena[7] == 0
    assert int(freq["frequencia"].sum()) == 18


def test_compute_atraso_counts_concursos_since_last() -> None:
    # Arrange.
    processed = process.process_concursos(_valid_history())
    # Act.
    atraso = process.compute_atraso(processed)
    # Assert: 0 in last concurso, 1 one concurso ago, 2 two ago, len(df) never seen.
    by_dezena = dict(zip(atraso["dezena"], atraso["atraso"]))
    assert by_dezena[10] == 0  # seen in concurso 3 (last)
    assert by_dezena[4] == 1  # last seen in concurso 2
    assert by_dezena[33] == 2  # last seen in concurso 1
    assert by_dezena[7] == 3  # never seen in 3 concursos


def test_process_accepts_string_dezenas_coerced() -> None:
    # Arrange: dezenas as strings (CSV-text shape), one with whitespace.
    raw = pd.DataFrame(
        [[1, "1996-03-11", "4", " 5 ", "30", "33", "41", "52"]],
        columns=HEADER,
    )
    # Act.
    out = process.process_concursos(raw)
    # Assert: coerced to ints, known-good soma 165.
    assert out.iloc[0][["dezena_1", "dezena_2"]].tolist() == [4, 5]
    assert int(out.iloc[0]["soma"]) == 165


def test_process_rejects_non_numeric_string() -> None:
    # Arrange: dezena "abc" cannot be coerced to int.
    raw = pd.DataFrame(
        [[1, "1996-03-11", "abc", 5, 30, 33, 41, 52]],
        columns=HEADER,
    )
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(inválida|invalid|inteiros)"):
        process.process_concursos(raw)


def test_process_accepts_float_integral_dezena() -> None:
    # Arrange: 4.0/5.0 are integral floats (pandas may surface floats).
    raw = pd.DataFrame(
        [[1, "1996-03-11", 4.0, 5.0, 30.0, 33.0, 41.0, 52.0]],
        columns=HEADER,
    )
    # Act.
    out = process.process_concursos(raw)
    # Assert.
    assert int(out.iloc[0]["soma"]) == 165


@pytest.mark.parametrize("bad_value", [4.5, 5.1, 30.99])
def test_process_rejects_float_non_integral_dezena(bad_value: float) -> None:
    # Arrange: non-integral float in the first dezena slot.
    raw = pd.DataFrame(
        [[1, "1996-03-11", bad_value, 5, 30, 33, 41, 52]],
        columns=HEADER,
    )
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(inválida|invalid|inteiros)"):
        process.process_concursos(raw)


@pytest.mark.parametrize("bad_value", [True, False])
def test_process_rejects_bool_dezena(bad_value: bool) -> None:
    # Arrange: bool is not a valid dezena even though bool is int subclass.
    raw = pd.DataFrame(
        [[1, "1996-03-11", bad_value, 5, 30, 33, 41, 52]],
        columns=HEADER,
    )
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(inválida|invalid|inteiros)"):
        process.process_concursos(raw)


def test_process_rejects_unknown_dezena_type() -> None:
    # Arrange: list object cannot be coerced to a dezena int.
    raw = pd.DataFrame(
        [[1, "1996-03-11", [4], 5, 30, 33, 41, 52]],
        columns=HEADER,
    )
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(inválida|invalid|inteiros)"):
        process.process_concursos(raw)


def test_validate_rejects_missing_column() -> None:
    # Arrange: frame without dezena_6.
    raw = pd.DataFrame(
        [[1, "1996-03-11", 4, 5, 30, 33, 41]],
        columns=[
            "concurso",
            "data",
            "dezena_1",
            "dezena_2",
            "dezena_3",
            "dezena_4",
            "dezena_5",
        ],
    )
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(coluna|column|ausente)"):
        process.validate_concursos(raw)


@pytest.mark.parametrize("bad_concurso", [None])
def test_process_rejects_null_concurso(bad_concurso: object) -> None:
    # Arrange: concurso identifier missing.
    raw = pd.DataFrame(
        [[bad_concurso, "1996-03-11", 4, 5, 30, 33, 41, 52]],
        columns=HEADER,
    )
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(ausente|nulo|null|número|numero)"):
        process.process_concursos(raw)


def test_process_does_not_mutate_input() -> None:
    # Arrange: unsorted concursos and unsorted dezenas.
    raw = pd.DataFrame(
        [
            [3, "1996-03-25", 60, 10, 50, 20, 40, 30],
            [1, "1996-03-11", 52, 4, 33, 5, 41, 30],
        ],
        columns=HEADER,
    )
    snapshot = raw.copy(deep=True)
    # Act.
    process.process_concursos(raw)
    # Assert: input frame identical (nunca altera o original).
    pd.testing.assert_frame_equal(raw, snapshot)


def test_process_normalizes_dezenas_ascending() -> None:
    # Arrange: dezenas out of order in a single jogo.
    raw = pd.DataFrame(
        [[1, "1996-03-11", 52, 4, 33, 5, 41, 30]],
        columns=HEADER,
    )
    # Act.
    out = process.process_concursos(raw)
    # Assert: dezenas sorted ascending within the jogo.
    assert out.iloc[0][
        ["dezena_1", "dezena_2", "dezena_3", "dezena_4", "dezena_5", "dezena_6"]
    ].tolist() == [4, 5, 30, 33, 41, 52]


@pytest.mark.parametrize(
    ("dezenas", "soma"),
    [([1, 2, 3, 4, 5, 6], 21), ([55, 56, 57, 58, 59, 60], 345)],
)
def test_process_soma_boundaries(dezenas: list[int], soma: int) -> None:
    # Arrange: minimum and maximum possible jogos.
    raw = pd.DataFrame(
        [[1, "1996-03-11", *dezenas]],
        columns=HEADER,
    )
    # Act.
    out = process.process_concursos(raw)
    # Assert: known-good boundary sums.
    assert int(out.iloc[0]["soma"]) == soma


@pytest.mark.parametrize(
    ("dezenas", "n_pares", "n_impares"),
    [([1, 3, 5, 7, 9, 11], 0, 6), ([2, 4, 6, 8, 10, 12], 6, 0)],
)
def test_process_parity_boundaries(
    dezenas: list[int], n_pares: int, n_impares: int
) -> None:
    # Arrange: all-odd and all-even jogos.
    raw = pd.DataFrame(
        [[1, "1996-03-11", *dezenas]],
        columns=HEADER,
    )
    # Act.
    out = process.process_concursos(raw)
    # Assert.
    assert int(out.iloc[0]["n_pares"]) == n_pares
    assert int(out.iloc[0]["n_impares"]) == n_impares
    assert int(out.iloc[0]["n_pares"]) + int(out.iloc[0]["n_impares"]) == 6


def test_process_is_idempotent_on_processed_output() -> None:
    # Arrange: already-processed frame.
    processed = process.process_concursos(_valid_history())
    # Act: process the processed output again.
    second = process.process_concursos(processed)
    # Assert: fixed point (reprocessar gera o mesmo resultado).
    pd.testing.assert_frame_equal(processed, second)


def test_compute_frequencia_covers_all_60_dezenas() -> None:
    # Arrange.
    processed = process.process_concursos(_valid_history())
    # Act.
    freq = process.compute_frequencia(processed)
    # Assert: one row per dezena 1-60, total slots 3 concursos x 6.
    assert list(freq.columns) == ["dezena", "frequencia"]
    assert list(freq["dezena"]) == list(range(1, 61))
    assert int(freq["frequencia"].sum()) == 18


def test_compute_frequencia_rejects_empty() -> None:
    # Arrange: empty frame with canonical columns.
    raw = pd.DataFrame(columns=HEADER)
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(vazio|empty)"):
        process.compute_frequencia(raw)


def test_compute_atraso_rejects_empty() -> None:
    # Arrange: empty frame with canonical columns.
    raw = pd.DataFrame(columns=HEADER)
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(vazio|empty)"):
        process.compute_atraso(raw)


def test_compute_atraso_single_concurso() -> None:
    # Arrange: a single concurso.
    processed = process.process_concursos(
        pd.DataFrame(
            [[1, "1996-03-11", 4, 5, 30, 33, 41, 52]],
            columns=HEADER,
        )
    )
    # Act.
    atraso = process.compute_atraso(processed)
    # Assert: drawn -> 0, never seen in 1 concurso -> 1.
    by_dezena = dict(zip(atraso["dezena"], atraso["atraso"]))
    assert by_dezena[4] == 0
    assert by_dezena[52] == 0
    assert by_dezena[7] == 1


def test_compute_atraso_ignores_input_order() -> None:
    # Arrange: same concursos in reverse order (unsorted input).
    ordered = process.process_concursos(_valid_history())
    reversed_raw = _valid_history().iloc[::-1].reset_index(drop=True)
    # Act.
    from_unsorted = process.compute_atraso(reversed_raw)
    from_ordered = process.compute_atraso(ordered)
    # Assert: atraso is positional by concurso, not by row order.
    pd.testing.assert_frame_equal(from_unsorted, from_ordered)


def test_process_accepts_numpy_integers_with_object_dtype() -> None:
    # Arrange: numpy ints in an object-dtype frame (CSV/object shape).
    import numpy as np  # type: ignore[import-untyped]

    raw = pd.DataFrame(
        [
            [
                1,
                "1996-03-11",
                np.int64(4),
                np.int32(5),
                np.int64(30),
                np.int64(33),
                np.int64(41),
                np.int64(52),
            ]
        ],
        columns=HEADER,
        dtype=object,
    )
    # Act.
    out = process.process_concursos(raw)
    # Assert: accepted as integral 1-60, known-good soma 165.
    assert int(out.iloc[0]["soma"]) == 165


def test_process_accepts_numpy_float_integral_with_object_dtype() -> None:
    # Arrange: integral numpy floats in an object-dtype frame.
    import numpy as np  # type: ignore[import-untyped]

    raw = pd.DataFrame(
        [[1, "1996-03-11", np.float64(4.0), np.float32(5.0), 30, 33, 41, 52]],
        columns=HEADER,
        dtype=object,
    )
    # Act.
    out = process.process_concursos(raw)
    # Assert: accepted, known-good soma 165.
    assert int(out.iloc[0]["soma"]) == 165
