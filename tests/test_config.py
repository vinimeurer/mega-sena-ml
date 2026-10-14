"""Central configuration tests: defaults for the skeleton contract."""

from __future__ import annotations

import config


def test_config_defaults_match_skeleton_contract() -> None:
    # Arrange: defaults from config.py.
    # Act / Assert: domain constants for dezenas, jogos and palpites.
    assert config.CONTEST_COL == "concurso"
    assert config.DATE_COL == "data"
    assert config.DEZENA_COLS == (
        "dezena_1",
        "dezena_2",
        "dezena_3",
        "dezena_4",
        "dezena_5",
        "dezena_6",
    )
    assert config.NUMBERS_PER_GAME == 6
    assert config.MIN_DEZENA == 1
    assert config.MAX_DEZENA == 60
    assert config.NUM_GUESSES == 5
    assert config.RANDOM_SEED == 42


def test_config_dezena_range_fits_valid_jogo() -> None:
    # Arrange: range and game size.
    # Act: distinct dezenas available for one jogo.
    available = config.MAX_DEZENA - config.MIN_DEZENA + 1
    # Assert.
    assert config.MIN_DEZENA < config.MAX_DEZENA
    assert available >= config.NUMBERS_PER_GAME
    assert available == 60


def test_config_directories_point_to_expected_names() -> None:
    # Arrange: configured paths.
    # Act / Assert: directory names match the skeleton layout.
    assert config.DATA_RAW_DIR.name == "raw"
    assert config.DATA_PROCESSED_DIR.name == "processed"
    assert config.DATA_OUTPUTS_DIR.name == "outputs"
    assert config.MODELS_DIR.name == "models"
    assert config.NOTEBOOKS_DIR.name == "notebooks"
