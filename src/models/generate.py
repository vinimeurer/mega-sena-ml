"""Palpite generation: ranked strategy and random baseline (T-004).

Both generators return valid jogos (6 distinct sorted dezenas 1-60)
and are reproducible: the same seed yields the same palpites.
The ranked strategy only reweights past frequencia/atraso for
description; it does not predict future concursos.
"""

from __future__ import annotations

import numpy as np  # type: ignore[import-untyped]
import pandas as pd  # type: ignore[import-untyped]

import config
from src.models import rank

DEZENA_COLS: tuple[str, ...] = tuple(config.DEZENA_COLS)


def _require_positive_n(n: int) -> None:
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError(f"Quantidade inválida de palpites: {n!r}. Use inteiro >= 1.")


def _resolve_seed(seed: int | None) -> int:
    if seed is None:
        return int(config.RANDOM_SEED)
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError(  # noqa: TRY004 - domain contract is ValueError with message
            f"Semente inválida: {seed!r}. Use inteiro ou omita "
            f"(padrão {int(config.RANDOM_SEED)})."
        )
    return seed


def generate_random_palmites(
    n: int = config.NUM_GUESSES, seed: int | None = config.RANDOM_SEED
) -> pd.DataFrame:
    """Generate n uniform random jogos (baseline, deterministic per seed)."""
    _require_positive_n(n)
    resolved = _resolve_seed(seed)
    rng = np.random.default_rng(resolved)
    pool = np.arange(config.MIN_DEZENA, config.MAX_DEZENA + 1)
    rows = []
    for _ in range(n):
        drawn = rng.choice(pool, size=config.NUMBERS_PER_GAME, replace=False)
        rows.append(sorted(int(v) for v in drawn.tolist()))
    return pd.DataFrame(rows, columns=list(DEZENA_COLS))


def generate_ranked_palmites(
    history: pd.DataFrame,
    n: int = config.NUM_GUESSES,
    seed: int | None = config.RANDOM_SEED,
    strategy: str = "combinada",
) -> pd.DataFrame:
    """Generate n jogos biased toward top-ranked dezenas (deterministic).

    Weights are (score + 1.0) so every dezena keeps positive probability
    while top-ranked dezenas are sampled more often. Raises ValueError
    on empty history, invalid n, invalid seed or unknown strategy.
    """
    _require_positive_n(n)
    resolved = _resolve_seed(seed)
    if history.empty:
        raise ValueError("Dado vazio: sem concursos para gerar palpites.")
    ranked = rank.rank_dezenas(history, strategy=strategy)
    dezenas = ranked["dezena"].to_numpy(dtype=int)
    weights = (ranked["score"].to_numpy(dtype=float) + 1.0).astype(float)
    probabilities = weights / weights.sum()
    rng = np.random.default_rng(resolved)
    rows = []
    for _ in range(n):
        drawn = rng.choice(
            dezenas, size=config.NUMBERS_PER_GAME, replace=False, p=probabilities
        )
        rows.append(sorted(int(v) for v in drawn.tolist()))
    return pd.DataFrame(rows, columns=list(DEZENA_COLS))
