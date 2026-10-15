"""Model generate tests: ranked palpites and random baseline."""

from __future__ import annotations

import pandas as pd  # type: ignore[import-untyped]
import pytest

import config
from src.models import generate

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


def _assert_valid_jogos(df: pd.DataFrame, n: int) -> None:
    assert list(df.columns) == DEZENA_COLS
    assert len(df) == n
    for _, row in df.iterrows():
        jogo = [int(v) for v in row.tolist()]
        assert len(jogo) == 6
        assert len(set(jogo)) == 6
        assert all(1 <= v <= 60 for v in jogo)
        assert jogo == sorted(jogo)


def test_generate_random_n_valid_jogos() -> None:
    # Arrange: default seed from config.
    # Act.
    out = generate.generate_random_palmites(n=5, seed=42)
    # Assert: 5 valid jogos, sorted distinct 1-60.
    _assert_valid_jogos(out, 5)


def test_generate_random_single_palpite_edge() -> None:
    # Arrange: smallest valid request.
    # Act.
    out = generate.generate_random_palmites(n=1, seed=42)
    # Assert: one valid jogo.
    _assert_valid_jogos(out, 1)


def test_generate_random_reproducible_same_seed() -> None:
    # Arrange: same seed twice.
    # Act.
    first = generate.generate_random_palmites(n=5, seed=7)
    second = generate.generate_random_palmites(n=5, seed=7)
    # Assert: identical frames.
    pd.testing.assert_frame_equal(first, second)


def test_generate_random_default_seed_matches_config() -> None:
    # Arrange: omitted seed must use the documented default.
    # Act.
    default = generate.generate_random_palmites(n=3)
    explicit = generate.generate_random_palmites(n=3, seed=config.RANDOM_SEED)
    # Assert.
    pd.testing.assert_frame_equal(default, explicit)


def test_generate_random_rejects_invalid_n() -> None:
    # Arrange: zero palpites requested.
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(n|palpite|positiv)"):
        generate.generate_random_palmites(n=0, seed=42)


def test_generate_ranked_n_valid_jogos() -> None:
    # Arrange: small history.
    history = _history()
    # Act.
    out = generate.generate_ranked_palmites(history, n=5, seed=42)
    # Assert: 5 valid jogos.
    _assert_valid_jogos(out, 5)


def test_generate_ranked_single_palpite_edge() -> None:
    # Arrange.
    history = _history()
    # Act.
    out = generate.generate_ranked_palmites(history, n=1, seed=42)
    # Assert.
    _assert_valid_jogos(out, 1)


def test_generate_ranked_reproducible_same_seed() -> None:
    # Arrange.
    history = _history()
    # Act.
    first = generate.generate_ranked_palmites(history, n=5, seed=123)
    second = generate.generate_ranked_palmites(history, n=5, seed=123)
    # Assert.
    pd.testing.assert_frame_equal(first, second)


def test_generate_ranked_default_seed_matches_config() -> None:
    # Arrange.
    history = _history()
    # Act.
    default = generate.generate_ranked_palmites(history, n=3)
    explicit = generate.generate_ranked_palmites(history, n=3, seed=config.RANDOM_SEED)
    # Assert: omitted seed uses the documented default.
    pd.testing.assert_frame_equal(default, explicit)


def test_generate_ranked_rejects_empty_history() -> None:
    # Arrange: empty frame.
    empty = pd.DataFrame(columns=HEADER)
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(vazio|empty)"):
        generate.generate_ranked_palmites(empty, n=2, seed=42)


def test_generate_ranked_rejects_invalid_n() -> None:
    # Arrange.
    history = _history()
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(n|palpite|positiv)"):
        generate.generate_ranked_palmites(history, n=0, seed=42)


def test_generate_ranked_rejects_unknown_strategy() -> None:
    # Arrange.
    history = _history()
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(strat|estrateg)"):
        generate.generate_ranked_palmites(history, n=2, seed=42, strategy="oraculo")


def test_generate_random_none_seed_uses_default() -> None:
    # Arrange: explicit None must fall back to the documented default.
    # Act.
    via_none = generate.generate_random_palmites(n=3, seed=None)
    explicit = generate.generate_random_palmites(n=3, seed=config.RANDOM_SEED)
    # Assert.
    pd.testing.assert_frame_equal(via_none, explicit)


def test_generate_ranked_none_seed_uses_default() -> None:
    # Arrange.
    history = _history()
    # Act.
    via_none = generate.generate_ranked_palmites(history, n=3, seed=None)
    explicit = generate.generate_ranked_palmites(history, n=3, seed=config.RANDOM_SEED)
    # Assert: omitted seed uses the documented default.
    pd.testing.assert_frame_equal(via_none, explicit)


@pytest.mark.parametrize("bad_seed", ["42", 4.5, True])
def test_generate_random_invalid_seed_type_rejects(bad_seed: object) -> None:
    # Arrange: seed outside the int-or-None contract.
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(semente|seed)"):
        generate.generate_random_palmites(
            n=2,
            seed=bad_seed,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("bad_seed", ["42", 4.5, True])
def test_generate_ranked_invalid_seed_type_rejects(bad_seed: object) -> None:
    # Arrange.
    history = _history()
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(semente|seed)"):
        generate.generate_ranked_palmites(
            history,
            n=2,
            seed=bad_seed,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("bad_n", [0, -1, True, "5", 2.5, None])
def test_generate_random_invalid_n_rejects(bad_n: object) -> None:
    # Arrange: n outside the int >= 1 contract (boundaries included).
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(n|palpite|positiv|ntegro|valid)"):
        generate.generate_random_palmites(
            n=bad_n,  # type: ignore[arg-type]
            seed=42,
        )


@pytest.mark.parametrize("bad_n", [0, -1, False, "5", 2.5])
def test_generate_ranked_invalid_n_rejects(bad_n: object) -> None:
    # Arrange.
    history = _history()
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(n|palpite|positiv|ntegro|valid)"):
        generate.generate_ranked_palmites(
            history,
            n=bad_n,  # type: ignore[arg-type]
            seed=42,
        )


def test_generate_random_different_seeds_differ() -> None:
    # Arrange: two distinct seeds.
    # Act.
    first = generate.generate_random_palmites(n=5, seed=1)
    second = generate.generate_random_palmites(n=5, seed=2)
    # Assert: honest baseline varies with the seed (deterministic check).
    assert not first.equals(second)


def test_generate_stays_within_limites_1_and_60() -> None:
    # Arrange: large deterministic sample touches the allowed interval.
    history = _history()
    # Act.
    random_out = generate.generate_random_palmites(n=50, seed=42)
    ranked_out = generate.generate_ranked_palmites(history, n=50, seed=42)
    # Assert: every dezena stays within 1-60, distinct and sorted.
    for out in (random_out, ranked_out):
        values = out[DEZENA_COLS].to_numpy(dtype=int)
        assert values.min() >= 1
        assert values.max() <= 60
        _assert_valid_jogos(out, len(out))
