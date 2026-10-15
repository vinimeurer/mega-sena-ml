"""Dezena ranking by frequencia and atraso (T-004).

The ranking is descriptive: it orders dezenas 1-60 by past frequency
and delay without promising future hits. Lottery draws are random.
"""

from __future__ import annotations

import pandas as pd  # type: ignore[import-untyped]

from src.data import process

STRATEGIES: tuple[str, ...] = ("frequencia", "atraso", "combinada")

RANK_COLUMNS: tuple[str, ...] = ("dezena", "frequencia", "atraso", "score")


def rank_dezenas(df: pd.DataFrame, strategy: str = "combinada") -> pd.DataFrame:
    """Rank dezenas 1-60 by the given strategy (deterministic).

    Strategies:
        frequencia: score is the past appearance count.
        atraso: score is the concursos since the last appearance.
        combinada: normalized frequencia plus normalized atraso.

    Returns a 60-row frame with columns dezena/frequencia/atraso/score,
    sorted by score desc, dezena asc. Raises ValueError on empty input
    or unknown strategy.
    """
    if strategy not in STRATEGIES:
        raise ValueError(
            f"Estratégia desconhecida: {strategy!r}. Use uma de {list(STRATEGIES)}."
        )
    if df.empty:
        raise ValueError("Dado vazio: sem concursos para ranquear dezenas.")
    freq = process.compute_frequencia(df)
    delay = process.compute_atraso(df)
    merged = freq.merge(delay, on="dezena", how="inner")
    if strategy == "frequencia":
        merged["score"] = merged["frequencia"].astype(float)
    elif strategy == "atraso":
        merged["score"] = merged["atraso"].astype(float)
    else:
        max_freq = float(merged["frequencia"].max())
        max_delay = float(merged["atraso"].max())
        freq_norm: pd.Series = (
            merged["frequencia"].astype(float) / max_freq
            if max_freq > 0
            else pd.Series(0.0, index=merged.index)
        )
        delay_norm: pd.Series = (
            merged["atraso"].astype(float) / max_delay
            if max_delay > 0
            else pd.Series(0.0, index=merged.index)
        )
        merged["score"] = (freq_norm + delay_norm).astype(float)
    ranked = merged.sort_values(
        by=["score", "dezena"], ascending=[False, True], kind="mergesort"
    ).reset_index(drop=True)
    return ranked[list(RANK_COLUMNS)].reset_index(drop=True)
