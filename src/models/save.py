"""Palpite CSV persistence with originating strategy (T-004)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]

import config

DEZENA_COLS: tuple[str, ...] = tuple(config.DEZENA_COLS)
STRATEGY_COL = "strategy"
PALPITES_COLUMNS: tuple[str, ...] = (*DEZENA_COLS, STRATEGY_COL)


def _validate_jogo(jogo: list[int]) -> None:
    if len(jogo) != config.NUMBERS_PER_GAME:
        raise ValueError(
            f"Jogo inválido {jogo}: todo palpite precisa de "
            f"{config.NUMBERS_PER_GAME} dezenas."
        )
    if len(set(jogo)) != len(jogo):
        raise ValueError(
            f"Jogo inválido {jogo}: dezenas repetidas. "
            "Cada palpite precisa de 6 dezenas distintas."
        )
    for dezena in jogo:
        if dezena < config.MIN_DEZENA or dezena > config.MAX_DEZENA:
            raise ValueError(
                f"Jogo inválido {jogo}: dezena {dezena} fora do intervalo "
                f"{config.MIN_DEZENA}-{config.MAX_DEZENA}."
            )
    if jogo != sorted(jogo):
        raise ValueError(
            f"Jogo inválido {jogo}: dezenas devem estar ordenadas em ordem crescente."
        )


def save_palmites(df: pd.DataFrame, path: str | Path) -> Path:
    """Save palpites as CSV without index (overwrite, deterministic).

    Requires dezena_1..dezena_6 plus the strategy column; every jogo
    must hold 6 distinct sorted dezenas 1-60. Raises ValueError otherwise.
    """
    if df.empty:
        raise ValueError("Dado vazio: nada para salvar em palpites.csv.")
    missing = [col for col in PALPITES_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"CSV inválido: colunas ausentes {missing}. "
            f"Esperado: {', '.join(PALPITES_COLUMNS)}."
        )
    for _, row in df.iterrows():
        _validate_jogo([int(row[col]) for col in DEZENA_COLS])
        strategy = row[STRATEGY_COL]
        if not isinstance(strategy, str) or not strategy.strip():
            raise ValueError(
                "Estratégia ausente: todo palpite precisa da estratégia de origem."
            )
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    df[list(PALPITES_COLUMNS)].to_csv(target, index=False)
    return target
