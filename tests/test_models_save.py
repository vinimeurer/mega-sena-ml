"""Model save tests: palpites CSV with strategy, no index."""

from __future__ import annotations

from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pytest

from src.models import save

DEZENA_COLS = [
    "dezena_1",
    "dezena_2",
    "dezena_3",
    "dezena_4",
    "dezena_5",
    "dezena_6",
]


def _palpites() -> pd.DataFrame:
    return pd.DataFrame(
        [
            [4, 5, 30, 33, 41, 52, "combinada"],
            [1, 2, 3, 4, 5, 60, "aleatoria"],
        ],
        columns=[*DEZENA_COLS, "strategy"],
    )


def test_save_palmites_csv_without_index(tmp_path: Path) -> None:
    # Arrange.
    df = _palpites()
    target = tmp_path / "palpites.csv"
    # Act.
    saved = save.save_palmites(df, target)
    # Assert: strategy column kept, no index column, rows preserved.
    assert saved == target
    text = target.read_text(encoding="utf-8")
    header = text.splitlines()[0]
    assert "Unnamed" not in header
    assert header.split(",") == [*DEZENA_COLS, "strategy"]
    reloaded = pd.read_csv(target)
    assert len(reloaded) == 2
    assert list(reloaded["strategy"]) == ["combinada", "aleatoria"]
    assert reloaded.iloc[0][DEZENA_COLS].tolist() == [4, 5, 30, 33, 41, 52]


def test_save_rejects_empty(tmp_path: Path) -> None:
    # Arrange.
    empty = pd.DataFrame()
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(vazio|empty)"):
        save.save_palmites(empty, tmp_path / "out.csv")


def test_save_rejects_missing_strategy(tmp_path: Path) -> None:
    # Arrange: frame without the strategy column.
    df = _palpites().drop(columns=["strategy"])
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(strategy|estrateg)"):
        save.save_palmites(df, tmp_path / "out.csv")


def test_save_rejects_invalid_jogo(tmp_path: Path) -> None:
    # Arrange: repeated dezena 5 in the first jogo.
    df = pd.DataFrame(
        [[5, 5, 30, 33, 41, 52, "combinada"]],
        columns=[*DEZENA_COLS, "strategy"],
    )
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(repetid|duplicat|distint)"):
        save.save_palmites(df, tmp_path / "out.csv")


def test_save_rejects_unsorted_jogo(tmp_path: Path) -> None:
    # Arrange: dezenas out of order.
    df = pd.DataFrame(
        [[52, 4, 33, 5, 41, 30, "combinada"]],
        columns=[*DEZENA_COLS, "strategy"],
    )
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(orden|sort)"):
        save.save_palmites(df, tmp_path / "out.csv")


def test_save_is_deterministic(tmp_path: Path) -> None:
    # Arrange.
    df = _palpites()
    target = tmp_path / "palpites.csv"
    # Act: save twice.
    save.save_palmites(df, target)
    first = target.read_bytes()
    save.save_palmites(df, target)
    second = target.read_bytes()
    # Assert.
    assert first == second


def test_save_creates_parent_dirs(tmp_path: Path) -> None:
    # Arrange.
    df = _palpites()
    target = tmp_path / "nested" / "dir" / "palpites.csv"
    # Act.
    save.save_palmites(df, target)
    # Assert.
    assert target.is_file()


def test_save_accepts_str_path(tmp_path: Path) -> None:
    # Arrange.
    df = _palpites()
    target = tmp_path / "palpites.csv"
    # Act.
    saved = save.save_palmites(df, str(target))
    # Assert.
    assert saved == target
    assert target.is_file()


def test_save_accepts_boundary_jogo_limits_1_and_60(tmp_path: Path) -> None:
    # Arrange: N=1 edge with dezenas on both limits.
    df = pd.DataFrame(
        [[1, 2, 3, 4, 5, 60, "combinada"]],
        columns=[*DEZENA_COLS, "strategy"],
    )
    target = tmp_path / "palpites.csv"
    # Act.
    saved = save.save_palmites(df, target)
    # Assert: boundary jogo persists and reloads unchanged.
    assert saved == target
    reloaded = pd.read_csv(target)
    assert reloaded.iloc[0][DEZENA_COLS].tolist() == [1, 2, 3, 4, 5, 60]


@pytest.mark.parametrize("bad_dezena", [0, 61])
def test_save_rejects_out_of_range_dezena(tmp_path: Path, bad_dezena: int) -> None:
    # Arrange: jogo with one dezena outside 1-60.
    jogo = [1, 2, 3, 4, 5, bad_dezena]
    df = pd.DataFrame(
        [[*sorted(jogo), "combinada"]],
        columns=[*DEZENA_COLS, "strategy"],
    )
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(intervalo|fora|1.*60)"):
        save.save_palmites(df, tmp_path / "out.csv")


@pytest.mark.parametrize("jogo", [[1, 2, 3, 4, 5]])
def test_save_rejects_wrong_jogo_length(tmp_path: Path, jogo: list[int]) -> None:
    # Arrange: frame with fewer than 6 dezena columns (missing dezena_6).
    df = pd.DataFrame(
        [[*jogo, "combinada"]],
        columns=[*([f"dezena_{i + 1}" for i in range(len(jogo))]), "strategy"],
    )
    # Act / Assert: rejected as missing column (save always reads 6 cols,
    # so the len != 6 guard in _validate_jogo is defensive; see FINDINGS).
    with pytest.raises(ValueError, match=r"(?i)(coluna|ausente|missing)"):
        save.save_palmites(df, tmp_path / "out.csv")


@pytest.mark.parametrize("bad_strategy", ["", "   "])
def test_save_rejects_blank_strategy(tmp_path: Path, bad_strategy: str) -> None:
    # Arrange: empty or whitespace-only strategy label.
    df = pd.DataFrame(
        [[1, 2, 3, 4, 5, 60, bad_strategy]],
        columns=[*DEZENA_COLS, "strategy"],
    )
    # Act / Assert.
    with pytest.raises(ValueError, match=r"(?i)(estrat|ausente|strategy)"):
        save.save_palmites(df, tmp_path / "out.csv")


def test_save_generated_palmites_roundtrip_valid(tmp_path: Path) -> None:
    # Arrange: end-to-end via the highest seam (generate -> save -> reload).
    from src.models import generate

    ranked = generate.generate_ranked_palmites(
        pd.DataFrame(
            [[1, "1996-03-11", 4, 5, 30, 33, 41, 52]],
            columns=[
                "concurso",
                "data",
                "dezena_1",
                "dezena_2",
                "dezena_3",
                "dezena_4",
                "dezena_5",
                "dezena_6",
            ],
        ),
        n=1,
        seed=42,
    ).assign(strategy="combinada")
    baseline = generate.generate_random_palmites(n=1, seed=42).assign(
        strategy="aleatoria"
    )
    df = pd.concat([ranked, baseline], ignore_index=True)
    target = tmp_path / "palpites.csv"
    # Act.
    save.save_palmites(df, target)
    # Assert: palpites.csv format (N rows + strategy, no index column).
    text = target.read_text(encoding="utf-8")
    assert text.splitlines()[0].split(",") == [*DEZENA_COLS, "strategy"]
    assert "Unnamed" not in text
    reloaded = pd.read_csv(target)
    assert len(reloaded) == 2
    assert list(reloaded["strategy"]) == ["combinada", "aleatoria"]
    for _, row in reloaded.iterrows():
        jogo = [int(row[col]) for col in DEZENA_COLS]
        assert len(set(jogo)) == 6
        assert all(1 <= v <= 60 for v in jogo)
        assert jogo == sorted(jogo)
