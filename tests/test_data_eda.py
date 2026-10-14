"""EDA helper tests: parity distribution, soma summary, co-occurrence."""

from __future__ import annotations

from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pytest

from src.data import eda, load, process

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


def test_parity_distribution_counts_concursos_per_n_pares() -> None:
    # Arrange: c1 has 3 pares, c2 has 3 pares, c3 has 6 pares.
    raw = _valid_history()
    # Act.
    out = eda.compute_parity_distribution(raw)
    # Assert: one row per 0..6, known-good literals, total is 3 concursos.
    assert list(out.columns) == ["n_pares", "concursos"]
    assert list(out["n_pares"]) == [0, 1, 2, 3, 4, 5, 6]
    by_pares = dict(zip(out["n_pares"], out["concursos"]))
    assert by_pares[3] == 2
    assert by_pares[6] == 1
    assert by_pares[0] == 0
    assert int(out["concursos"].sum()) == 3


def test_parity_distribution_single_concurso() -> None:
    # Arrange: single all-odd jogo (0 pares).
    raw = pd.DataFrame(
        [[1, "1996-03-11", 1, 3, 5, 7, 9, 11]],
        columns=HEADER,
    )
    # Act.
    out = eda.compute_parity_distribution(raw)
    # Assert: still 7 rows so a small history renders; total is 1.
    assert len(out) == 7
    by_pares = dict(zip(out["n_pares"], out["concursos"]))
    assert by_pares[0] == 1
    assert int(out["concursos"].sum()) == 1


def test_parity_distribution_rejects_empty() -> None:
    # Arrange.
    raw = pd.DataFrame(columns=HEADER)
    # Act / Assert.
    try:
        eda.compute_parity_distribution(raw)
    except ValueError as exc:
        assert "vazio" in str(exc).lower() or "empty" in str(exc).lower()
    else:
        raise AssertionError("expected ValueError for empty frame")


def test_soma_summary_known_values() -> None:
    # Arrange: somas 165, 75, 210.
    raw = _valid_history()
    # Act.
    out = eda.compute_soma_summary(raw)
    # Assert: known-good literals (not recomputed by the test).
    assert out["count"] == 3
    assert out["min"] == 75
    assert out["max"] == 210
    assert out["mean"] == 150.0
    assert out["median"] == 165.0


def test_soma_summary_single_concurso() -> None:
    # Arrange: single jogo 4+5+30+33+41+52=165.
    raw = pd.DataFrame(
        [[1, "1996-03-11", 4, 5, 30, 33, 41, 52]],
        columns=HEADER,
    )
    # Act.
    out = eda.compute_soma_summary(raw)
    # Assert: min/max/mean/median collapse to the single soma.
    assert out["count"] == 1
    assert out["min"] == 165
    assert out["max"] == 165
    assert out["mean"] == 165.0
    assert out["median"] == 165.0


def test_soma_summary_rejects_empty() -> None:
    # Arrange.
    raw = pd.DataFrame(columns=HEADER)
    # Act / Assert.
    try:
        eda.compute_soma_summary(raw)
    except ValueError as exc:
        assert "vazio" in str(exc).lower() or "empty" in str(exc).lower()
    else:
        raise AssertionError("expected ValueError for empty frame")


def test_cooccurrence_diagonal_matches_frequencia() -> None:
    # Arrange.
    raw = _valid_history()
    # Act.
    matrix = eda.compute_cooccurrence_matrix(raw)
    # Assert: 60x60 indexed 1..60; dezena 4 in 2 jogos, 7 in none.
    assert matrix.shape == (60, 60)
    assert list(matrix.index) == list(range(1, 61))
    assert list(matrix.columns) == list(range(1, 61))
    assert int(matrix.loc[4, 4]) == 2
    assert int(matrix.loc[60, 60]) == 2
    assert int(matrix.loc[7, 7]) == 0


def test_cooccurrence_off_diagonal_counts_shared_concursos() -> None:
    # Arrange.
    raw = _valid_history()
    # Act.
    matrix = eda.compute_cooccurrence_matrix(raw)
    # Assert: known-good literals; (4,5) together in c1+c2, (4,10) never.
    assert int(matrix.loc[4, 5]) == 2
    assert int(matrix.loc[5, 4]) == 2
    assert int(matrix.loc[4, 30]) == 1
    assert int(matrix.loc[10, 20]) == 1
    assert int(matrix.loc[4, 10]) == 0


def test_cooccurrence_is_symmetric_and_single_concurso() -> None:
    # Arrange: single jogo.
    raw = pd.DataFrame(
        [[1, "1996-03-11", 4, 5, 30, 33, 41, 52]],
        columns=HEADER,
    )
    # Act.
    matrix = eda.compute_cooccurrence_matrix(raw)
    # Assert: symmetric, drawn pairs are 1, unseen dezena 7 row is all zero.
    pd.testing.assert_frame_equal(matrix, matrix.T)
    assert int(matrix.loc[4, 5]) == 1
    assert int(matrix.loc[4, 4]) == 1
    assert int(matrix.loc[7, 7]) == 0
    assert int(matrix.loc[7, 4]) == 0


def test_cooccurrence_rejects_empty() -> None:
    # Arrange.
    raw = pd.DataFrame(columns=HEADER)
    # Act / Assert.
    try:
        eda.compute_cooccurrence_matrix(raw)
    except ValueError as exc:
        assert "vazio" in str(exc).lower() or "empty" in str(exc).lower()
    else:
        raise AssertionError("expected ValueError for empty frame")


@pytest.mark.parametrize(
    "helper",
    ["parity", "soma", "cooccurrence"],
)
def test_eda_helper_missing_dezena_column_rejects(helper: str) -> None:
    # Arrange: frame without dezena_6 (uncovered _require_dezenas branch).
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
    func = {
        "parity": eda.compute_parity_distribution,
        "soma": eda.compute_soma_summary,
        "cooccurrence": eda.compute_cooccurrence_matrix,
    }[helper]
    with pytest.raises(ValueError, match=r"(?i)(coluna|column|ausente)"):
        func(raw)


@pytest.mark.parametrize(
    ("dezenas", "expected_pares"),
    [([1, 3, 5, 7, 9, 11], 0), ([2, 4, 6, 8, 10, 12], 6)],
)
def test_parity_distribution_boundary_extremes_counts(
    dezenas: list[int], expected_pares: int
) -> None:
    # Arrange: all-odd (0 pares) and all-even (6 pares) jogos.
    raw = pd.DataFrame(
        [[1, "1996-03-11", *dezenas]],
        columns=HEADER,
    )
    # Act.
    out = eda.compute_parity_distribution(raw)
    # Assert: still 7 rows; the extreme bucket holds the single concurso.
    assert len(out) == 7
    by_pares = dict(zip(out["n_pares"], out["concursos"]))
    assert by_pares[expected_pares] == 1
    assert int(out["concursos"].sum()) == 1


def test_parity_distribution_ignores_order_is_deterministic() -> None:
    # Arrange: same concursos with shuffled rows and unsorted dezenas.
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
    from_ordered = eda.compute_parity_distribution(ordered)
    from_shuffled = eda.compute_parity_distribution(shuffled)
    # Assert: order-independent and repeatable (deterministic).
    pd.testing.assert_frame_equal(from_ordered, from_shuffled)
    pd.testing.assert_frame_equal(
        from_ordered, eda.compute_parity_distribution(ordered)
    )


def test_parity_distribution_does_not_mutate_input() -> None:
    # Arrange.
    raw = _valid_history()
    snapshot = raw.copy(deep=True)
    # Act.
    eda.compute_parity_distribution(raw)
    # Assert: input frame identical.
    pd.testing.assert_frame_equal(raw, snapshot)


def test_soma_summary_even_count_median_averages_middle_two() -> None:
    # Arrange: two concursos with somas 165 and 75.
    raw = pd.DataFrame(
        [
            [1, "1996-03-11", 4, 5, 30, 33, 41, 52],
            [2, "1996-03-18", 1, 2, 3, 4, 5, 60],
        ],
        columns=HEADER,
    )
    # Act.
    out = eda.compute_soma_summary(raw)
    # Assert: known-good literals (median of 2 values is their average).
    assert out["count"] == 2
    assert out["min"] == 75
    assert out["max"] == 165
    assert out["mean"] == 120.0
    assert out["median"] == 120.0


@pytest.mark.parametrize(
    ("dezenas", "soma"),
    [([1, 2, 3, 4, 5, 6], 21), ([55, 56, 57, 58, 59, 60], 345)],
)
def test_soma_summary_boundaries_min_and_max(dezenas: list[int], soma: int) -> None:
    # Arrange: minimum and maximum possible jogos.
    raw = pd.DataFrame(
        [[1, "1996-03-11", *dezenas]],
        columns=HEADER,
    )
    # Act.
    out = eda.compute_soma_summary(raw)
    # Assert: known-good boundary sums collapse min/max/mean/median.
    assert out["count"] == 1
    assert out["min"] == soma
    assert out["max"] == soma
    assert out["mean"] == float(soma)
    assert out["median"] == float(soma)


def test_soma_summary_is_deterministic() -> None:
    # Arrange.
    raw = _valid_history()
    # Act.
    first = eda.compute_soma_summary(raw)
    second = eda.compute_soma_summary(raw)
    # Assert: same dict on repeated calls; keys are the documented contract.
    assert first == second
    assert set(first) == {"count", "min", "max", "mean", "median"}


def test_cooccurrence_ignores_order_is_deterministic() -> None:
    # Arrange: same jogos with shuffled rows and unsorted dezenas.
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
    from_ordered = eda.compute_cooccurrence_matrix(ordered)
    from_shuffled = eda.compute_cooccurrence_matrix(shuffled)
    # Assert: order-independent and repeatable.
    pd.testing.assert_frame_equal(from_ordered, from_shuffled)
    pd.testing.assert_frame_equal(
        from_ordered, eda.compute_cooccurrence_matrix(ordered)
    )


def test_cooccurrence_does_not_mutate_input() -> None:
    # Arrange.
    raw = _valid_history()
    snapshot = raw.copy(deep=True)
    # Act.
    eda.compute_cooccurrence_matrix(raw)
    # Assert: input frame identical.
    pd.testing.assert_frame_equal(raw, snapshot)


def test_cooccurrence_diagonal_sum_equals_six_per_concurso() -> None:
    # Arrange: 3 concursos, 6 dezenas each.
    raw = _valid_history()
    # Act.
    matrix = eda.compute_cooccurrence_matrix(raw)
    # Assert: diagonal holds frequencia (sum is 6 per concurso); symmetric.
    diag_sum = sum(int(matrix.loc[d, d]) for d in range(1, 61))
    assert diag_sum == 18
    pd.testing.assert_frame_equal(matrix, matrix.T)


def test_eda_pipeline_load_process_helpers_end_to_end(tmp_path: Path) -> None:
    # Arrange: canonical CSV through the highest agreed seam (load+process).
    csv_path = tmp_path / "concursos.csv"
    csv_path.write_text(
        "concurso,data,dezena_1,dezena_2,dezena_3,dezena_4,dezena_5,dezena_6\n"
        "1,1996-03-11,4,5,30,33,41,52\n"
        "2,1996-03-18,1,2,3,4,5,60\n"
        "3,1996-03-25,10,20,30,40,50,60\n",
        encoding="utf-8",
    )
    # Act.
    df = process.process_concursos(load.load_raw_csv(csv_path))
    parity = eda.compute_parity_distribution(df)
    summary = eda.compute_soma_summary(df)
    matrix = eda.compute_cooccurrence_matrix(df)
    # Assert: cross-helper invariants on the same 3 concursos.
    assert int(parity["concursos"].sum()) == 3
    assert summary["count"] == 3
    assert summary["min"] == 75
    assert summary["max"] == 210
    assert matrix.shape == (60, 60)
    pd.testing.assert_frame_equal(matrix, matrix.T)


def test_eda_helpers_on_real_history_satisfy_invariants() -> None:
    # Arrange: real processed history, as the notebook executes it.
    raw_path = Path(__file__).resolve().parent.parent / "data" / "raw" / "Mega-Sena.csv"
    if not raw_path.is_file():
        pytest.skip(f"real history not found: {raw_path}")
    df = process.process_concursos(load.load_raw_csv(raw_path))
    # Act.
    parity = eda.compute_parity_distribution(df)
    summary = eda.compute_soma_summary(df)
    matrix = eda.compute_cooccurrence_matrix(df)
    # Assert: invariants hold for any history size (no hardcoded counts).
    n = len(df)
    assert n > 0
    assert list(parity["n_pares"]) == [0, 1, 2, 3, 4, 5, 6]
    assert int(parity["concursos"].sum()) == n
    assert summary["count"] == n
    assert summary["min"] <= summary["mean"] <= summary["max"]
    assert summary["min"] <= summary["median"] <= summary["max"]
    assert matrix.shape == (60, 60)
    assert list(matrix.index) == list(range(1, 61))
    assert list(matrix.columns) == list(range(1, 61))
    diag_sum = sum(int(matrix.loc[d, d]) for d in range(1, 61))
    assert diag_sum == 6 * n
    pd.testing.assert_frame_equal(matrix, matrix.T)
