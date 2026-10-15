"""Model rank tests: dezena ranking by frequencia and atraso."""

from __future__ import annotations

import pandas as pd  # type: ignore[import-untyped]
import pytest

from src.models import rank

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


def test_rank_frequencia_top_is_most_frequent() -> None:
    # Arrange: 3 concursos, dezenas 4/5/30/60 appear twice.
    history = _history()
    # Act.
    ranked = rank.rank_dezenas(history, strategy="frequencia")
    # Assert: 60 rows, most frequent first with literal score 2.
    assert list(ranked.columns) == ["dezena", "frequencia", "atraso", "score"]
    assert len(ranked) == 60
    assert list(ranked["dezena"])[:4] == [4, 5, 30, 60]
    assert float(ranked.iloc[0]["score"]) == 2.0
    assert int(ranked.iloc[0]["frequencia"]) == 2


def test_rank_atraso_top_is_longest_absent() -> None:
    # Arrange.
    history = _history()
    # Act.
    ranked = rank.rank_dezenas(history, strategy="atraso")
    # Assert: never-seen dezena 6 first with literal atraso 3.
    assert len(ranked) == 60
    assert int(ranked.iloc[0]["dezena"]) == 6
    assert int(ranked.iloc[0]["atraso"]) == 3
    assert float(ranked.iloc[0]["score"]) == 3.0


def test_rank_combinada_balances_frequencia_and_atraso() -> None:
    # Arrange.
    history = _history()
    # Act.
    ranked = rank.rank_dezenas(history, strategy="combinada")
    # Assert: dezena 4 first; score = 1.0 (freq norm) + 1/3 (atraso norm).
    assert len(ranked) == 60
    assert int(ranked.iloc[0]["dezena"]) == 4
    assert float(ranked.iloc[0]["score"]) == pytest.approx(4 / 3)


def test_rank_default_strategy_is_combinada() -> None:
    # Arrange.
    history = _history()
    # Act.
    default = rank.rank_dezenas(history)
    explicit = rank.rank_dezenas(history, strategy="combinada")
    # Assert: same frame when seed strategy is omitted.
    pd.testing.assert_frame_equal(default, explicit)


def test_rank_rejects_unknown_strategy() -> None:
    # Arrange.
    history = _history()
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(strat|estrateg)"):
        rank.rank_dezenas(history, strategy="oraculo")


def test_rank_rejects_empty_history() -> None:
    # Arrange: empty frame with canonical columns.
    empty = pd.DataFrame(columns=HEADER)
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(vazio|empty)"):
        rank.rank_dezenas(empty, strategy="combinada")


def test_rank_covers_limites_1_and_60() -> None:
    # Arrange.
    history = _history()
    # Act.
    ranked = rank.rank_dezenas(history, strategy="combinada")
    # Assert: all 60 dezenas 1-60 appear exactly once (boundaries included).
    assert sorted(ranked["dezena"].tolist()) == list(range(1, 61))
    assert len(ranked) == 60


def test_rank_is_deterministic_same_input() -> None:
    # Arrange.
    history = _history()
    # Act.
    first = rank.rank_dezenas(history, strategy="combinada")
    second = rank.rank_dezenas(history, strategy="combinada")
    # Assert: same history yields the same ranking.
    pd.testing.assert_frame_equal(first, second)
