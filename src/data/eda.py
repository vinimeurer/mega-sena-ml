"""EDA helpers: parity distribution, soma summary and co-occurrence."""

from __future__ import annotations

import pandas as pd  # type: ignore[import-untyped]

import config

DEZENA_COLS: tuple[str, ...] = tuple(config.DEZENA_COLS)
MIN_DEZENA = config.MIN_DEZENA
MAX_DEZENA = config.MAX_DEZENA


def _require_dezenas(df: pd.DataFrame) -> None:
    """Validate the frame has dezenas to aggregate; raise ValueError if not."""
    missing = [col for col in DEZENA_COLS if col not in df.columns]
    if missing:
        raise ValueError(
            f"CSV inválido: colunas ausentes {missing}. "
            f"Esperado: {', '.join(DEZENA_COLS)}."
        )
    if df.empty:
        raise ValueError("Dado vazio: sem concursos para a análise EDA.")


def compute_parity_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Count concursos per number of pares (0-6).

    Returns one row per 0..6 so small histories still render a full chart.
    """
    _require_dezenas(df)
    n_pares = (df[list(DEZENA_COLS)] % 2 == 0).sum(axis=1).astype(int)
    counts = n_pares.value_counts()
    rows = [{"n_pares": n, "concursos": int(counts.get(n, 0))} for n in range(7)]
    return pd.DataFrame(rows, columns=["n_pares", "concursos"])


def compute_soma_summary(df: pd.DataFrame) -> dict[str, float]:
    """Summarize the per-concurso soma with count/min/max/mean/median."""
    _require_dezenas(df)
    somas = df[list(DEZENA_COLS)].sum(axis=1)
    return {
        "count": len(somas),
        "min": int(somas.min()),
        "max": int(somas.max()),
        "mean": float(somas.mean()),
        "median": float(somas.median()),
    }


def compute_cooccurrence_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Count concursos where each dezena pair appeared together.

    Diagonal holds the frequencia per dezena; off-diagonal holds the
    shared-concurso count. Symmetric 60x60 frame indexed/columned 1..60.
    """
    _require_dezenas(df)
    size = MAX_DEZENA - MIN_DEZENA + 1
    counts = [[0] * size for _ in range(size)]
    for _, row in df.iterrows():
        dezenas = sorted(int(row[col]) for col in DEZENA_COLS)
        for i, first in enumerate(dezenas):
            for second in dezenas[i:]:
                counts[first - MIN_DEZENA][second - MIN_DEZENA] += 1
                if second != first:
                    counts[second - MIN_DEZENA][first - MIN_DEZENA] += 1
    labels = list(range(MIN_DEZENA, MAX_DEZENA + 1))
    return pd.DataFrame(counts, index=labels, columns=labels)
