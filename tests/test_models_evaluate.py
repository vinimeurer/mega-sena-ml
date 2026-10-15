"""Model evaluate tests: descriptive metrics over history."""

from __future__ import annotations

import pandas as pd  # type: ignore[import-untyped]
import pytest

from src.models import evaluate

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
DEZENA_COLS = [
    "dezena_1",
    "dezena_2",
    "dezena_3",
    "dezena_4",
    "dezena_5",
    "dezena_6",
]


def _history() -> pd.DataFrame:
    from src.data import process

    raw = pd.DataFrame(
        [
            [1, "1996-03-11", 4, 5, 30, 33, 41, 52],
            [2, "1996-03-18", 1, 2, 3, 4, 5, 60],
            [3, "1996-03-25", 10, 20, 30, 40, 50, 60],
        ],
        columns=HEADER,
    )
    return process.process_concursos(raw)


def _palpite(jogo: list[int]) -> pd.DataFrame:
    return pd.DataFrame([sorted(jogo)], columns=DEZENA_COLS)


def test_count_hits_known_literal() -> None:
    # Arrange: palpite equals concurso 1.
    # Act.
    hits = evaluate.count_hits([4, 5, 30, 33, 41, 52], [1, 2, 3, 4, 5, 60])
    # Assert: intersection {4, 5} has size 2.
    assert hits == 2


def test_evaluate_single_palpite_known_literals() -> None:
    # Arrange: history of 3 concursos, palpite equals concurso 1.
    history = _history()
    palpites = _palpite([4, 5, 30, 33, 41, 52])
    # Act.
    metrics = evaluate.evaluate_palmites(history, palpites)
    # Assert: hits 6/2/1 -> mean 3.0, max 6; coverage 6/60; soma 165; pares 3.
    assert metrics["n_palmites"] == 1
    assert metrics["cobertura"] == pytest.approx(0.1)
    assert metrics["soma_media"] == pytest.approx(165.0)
    assert metrics["pares_medio"] == pytest.approx(3.0)
    assert metrics["acertos_medio"] == pytest.approx(3.0)
    assert metrics["acertos_max"] == 6


def test_evaluate_rejects_empty_history() -> None:
    # Arrange.
    empty = pd.DataFrame(columns=HEADER)
    palpites = _palpite([1, 2, 3, 4, 5, 6])
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(vazio|empty)"):
        evaluate.evaluate_palmites(empty, palpites)


def test_evaluate_rejects_empty_palpites() -> None:
    # Arrange.
    history = _history()
    empty = pd.DataFrame(columns=DEZENA_COLS)
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(vazio|empty)"):
        evaluate.evaluate_palmites(history, empty)


def test_compare_strategies_returns_one_row_per_strategy() -> None:
    # Arrange.
    history = _history()
    # Act.
    table = evaluate.compare_strategies(
        history, n=2, seed=42, strategies=("combinada", "aleatoria")
    )
    # Assert: shape, columns and strategy labels.
    assert list(table.columns) == [
        "strategy",
        "n_palmites",
        "cobertura",
        "soma_media",
        "pares_medio",
        "acertos_medio",
        "acertos_max",
    ]
    assert list(table["strategy"]) == ["combinada", "aleatoria"]
    assert list(table["n_palmites"]) == [2, 2]
    for col in ("cobertura", "soma_media", "pares_medio", "acertos_medio"):
        assert table[col].notna().all()


def test_compare_strategies_is_deterministic() -> None:
    # Arrange.
    history = _history()
    # Act.
    first = evaluate.compare_strategies(history, n=2, seed=9)
    second = evaluate.compare_strategies(history, n=2, seed=9)
    # Assert.
    pd.testing.assert_frame_equal(first, second)


def test_compare_strategies_rejects_unknown_strategy() -> None:
    # Arrange.
    history = _history()
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(strat|estrateg)"):
        evaluate.compare_strategies(history, n=1, seed=42, strategies=("oraculo",))


def test_evaluate_rejects_missing_history_column() -> None:
    # Arrange: history without dezena_6.
    history = _history().drop(columns=["dezena_6"])
    palpites = _palpite([1, 2, 3, 4, 5, 6])
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(coluna|missing|ausente)"):
        evaluate.evaluate_palmites(history, palpites)


def test_evaluate_rejects_missing_palpite_column() -> None:
    # Arrange: palpites without dezena_6.
    history = _history()
    palpites = _palpite([1, 2, 3, 4, 5, 6]).drop(columns=["dezena_6"])
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(coluna|missing|ausente)"):
        evaluate.evaluate_palmites(history, palpites)


def test_compare_strategies_rejects_empty_history() -> None:
    # Arrange: empty frame with canonical columns.
    empty = pd.DataFrame(columns=HEADER)
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(vazio|empty)"):
        evaluate.compare_strategies(empty, n=2, seed=42)


def test_compare_strategies_rejects_empty_strategies() -> None:
    # Arrange.
    history = _history()
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(estrat|strateg)"):
        evaluate.compare_strategies(history, n=2, seed=42, strategies=())


def test_compare_strategies_baseline_side_by_side() -> None:
    # Arrange: ranked strategy next to the honest random baseline.
    history = _history()
    # Act.
    table = evaluate.compare_strategies(
        history, n=2, seed=42, strategies=("combinada", "aleatoria")
    )
    # Assert: same N per strategy, metrics within valid ranges.
    assert list(table["strategy"]) == ["combinada", "aleatoria"]
    assert list(table["n_palmites"]) == [2, 2]
    assert ((table["cobertura"] > 0) & (table["cobertura"] <= 1)).all()
    assert ((table["acertos_medio"] >= 0) & (table["acertos_medio"] <= 6)).all()
    assert ((table["acertos_max"] >= 0) & (table["acertos_max"] <= 6)).all()


def test_compare_strategies_end_to_end_ranked_and_baseline() -> None:
    # Arrange: highest agreed seam (generation + evaluation in one call).
    from src.models import generate

    history = _history()
    # Act: N=1 boundary per strategy plus the comparison table.
    ranked = generate.generate_ranked_palmites(history, n=1, seed=42)
    baseline = generate.generate_random_palmites(n=1, seed=42)
    table = evaluate.compare_strategies(
        history, n=1, seed=42, strategies=("combinada", "aleatoria")
    )
    # Assert: single valid jogo each; table aggregates both strategies.
    assert len(ranked) == 1
    assert len(baseline) == 1
    assert list(table["strategy"]) == ["combinada", "aleatoria"]
    ranked_metrics = evaluate.evaluate_palmites(history, ranked)
    assert table.loc[0, "acertos_medio"] == pytest.approx(
        ranked_metrics["acertos_medio"]
    )
