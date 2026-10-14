"""Processed data persistence (CSV without index)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]

import config


def save_processed(df: pd.DataFrame, path: str | Path) -> Path:
    """Save processed concursos as CSV without index (overwrite, deterministic).

    Raises:
        ValueError: when the frame is empty, lacks the concurso column,
            or has duplicated concursos.
    """
    if df.empty:
        raise ValueError("Dado vazio: nada para salvar em CSV.")
    if config.CONTEST_COL not in df.columns:
        raise ValueError(
            f"CSV inválido: coluna ausente ['{config.CONTEST_COL}']. "
            "O processado exige um registro por concurso."
        )
    if bool(df[config.CONTEST_COL].duplicated().any()):
        raise ValueError(
            "CSV inválido: concurso duplicado. O processado exige um registro por concurso."
        )
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target, index=False)
    return target
