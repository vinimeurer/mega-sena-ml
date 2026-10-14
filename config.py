"""Central configuration for mega-sena-ml.

All paths, column names, guess counts, seeds and strategy parameters live
here. Values can be overridden through environment variables documented in
`.env.example`.
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATA_RAW_DIR = Path(os.getenv("MEGA_SENA_DATA_RAW", str(BASE_DIR / "data" / "raw")))
DATA_PROCESSED_DIR = Path(
    os.getenv("MEGA_SENA_DATA_PROCESSED", str(BASE_DIR / "data" / "processed"))
)
DATA_OUTPUTS_DIR = Path(
    os.getenv("MEGA_SENA_DATA_OUTPUTS", str(BASE_DIR / "data" / "outputs"))
)
MODELS_DIR = Path(os.getenv("MEGA_SENA_MODELS_DIR", str(BASE_DIR / "models")))
NOTEBOOKS_DIR = Path(os.getenv("MEGA_SENA_NOTEBOOKS_DIR", str(BASE_DIR / "notebooks")))

CONTEST_COL = os.getenv("MEGA_SENA_CONTEST_COL", "concurso")
DATE_COL = os.getenv("MEGA_SENA_DATE_COL", "data")
DEZENA_COLS = tuple(
    os.getenv(
        "MEGA_SENA_DEZENA_COLS", "dezena_1,dezena_2,dezena_3,dezena_4,dezena_5,dezena_6"
    ).split(",")
)

NUMBERS_PER_GAME = int(os.getenv("MEGA_SENA_NUMBERS_PER_GAME", "6"))
MIN_DEZENA = int(os.getenv("MEGA_SENA_MIN_DEZENA", "1"))
MAX_DEZENA = int(os.getenv("MEGA_SENA_MAX_DEZENA", "60"))

NUM_GUESSES = int(os.getenv("MEGA_SENA_NUM_GUESSES", "5"))
RANDOM_SEED = int(os.getenv("MEGA_SENA_RANDOM_SEED", "42"))
