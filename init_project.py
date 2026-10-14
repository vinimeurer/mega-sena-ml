"""Idempotent project directory initialization."""

from __future__ import annotations

from pathlib import Path

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/outputs",
    "notebooks",
    "src/data",
    "src/models",
    "tests",
    "models",
]


def ensure_directories(base_dir: Path | None = None) -> list[Path]:
    """Create required project directories if missing.

    Idempotent: safe to run multiple times, never deletes anything.
    """
    root = Path(base_dir) if base_dir is not None else Path(__file__).resolve().parent
    created: list[Path] = []
    for rel in REQUIRED_DIRS:
        path = root / rel
        path.mkdir(parents=True, exist_ok=True)
        created.append(path)
    return created


if __name__ == "__main__":
    paths = ensure_directories()
    for path in paths:
        print(f"ensured {path}")
