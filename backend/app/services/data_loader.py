import logging
from pathlib import Path

import pandas as pd

from app.core.config import (
    PROCESSED_GAMES_PATH,
    RAW_COACHES_PATH,
    RAW_GAMES_PATH,
    RAW_PLAYERS_PATH,
    RAW_UPCOMING_GAMES_PATH,
    REQUIRED_COACHES_COLUMNS,
    REQUIRED_GAMES_COLUMNS,
    REQUIRED_PLAYERS_COLUMNS,
    REQUIRED_UPCOMING_COLUMNS,
)

logger = logging.getLogger(__name__)


def _safe_read_csv(path: Path, required_columns: list[str]) -> pd.DataFrame:
    """Read a CSV, backfill missing columns, and return an empty DF on failure."""
    if not path.exists():
        logger.warning("File not found: %s — returning empty DataFrame", path)
        return pd.DataFrame(columns=required_columns)

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        logger.error("Failed to read %s: %s", path, exc)
        return pd.DataFrame(columns=required_columns)

    for col in required_columns:
        if col not in df.columns:
            logger.warning("Missing column '%s' in %s — adding with NaN", col, path.name)
            df[col] = pd.NA

    if "game_date" in df.columns:
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")

    if "division" in df.columns:
        before = len(df)
        df = df[df["division"].astype(str).str.upper().isin(["D1", "1", "DIVISION I"])]
        filtered = before - len(df)
        if filtered:
            logger.info("Filtered %d non-D1 rows from %s", filtered, path.name)

    return df


def load_games_df() -> pd.DataFrame:
    """Load historical games — prefer processed, fall back to raw."""
    if PROCESSED_GAMES_PATH.exists():
        logger.info("Loading processed games from %s", PROCESSED_GAMES_PATH)
        return _safe_read_csv(PROCESSED_GAMES_PATH, REQUIRED_GAMES_COLUMNS)

    logger.info("Processed games not found, falling back to raw: %s", RAW_GAMES_PATH)
    return _safe_read_csv(RAW_GAMES_PATH, REQUIRED_GAMES_COLUMNS)


def load_players_df() -> pd.DataFrame:
    """Load player game logs."""
    return _safe_read_csv(RAW_PLAYERS_PATH, REQUIRED_PLAYERS_COLUMNS)


def load_coaches_df() -> pd.DataFrame:
    """Load coach records."""
    return _safe_read_csv(RAW_COACHES_PATH, REQUIRED_COACHES_COLUMNS)


def load_upcoming_games_df() -> pd.DataFrame:
    """Load the upcoming games schedule."""
    return _safe_read_csv(RAW_UPCOMING_GAMES_PATH, REQUIRED_UPCOMING_COLUMNS)
