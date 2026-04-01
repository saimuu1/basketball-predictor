"""
clean_data.py
Cleans raw games CSV into a processed, model-ready dataset.

Usage (from backend/ directory):
    python -m app.scripts.clean_data
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import (
    RAW_GAMES_PATH,
    PROCESSED_DIR,
    PROCESSED_GAMES_PATH,
    REQUIRED_GAMES_COLUMNS,
)


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase, strip, and snake_case all column names."""
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w]+", "_", regex=True)
        .str.strip("_")
    )
    return df


def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    if "game_date" in df.columns:
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
    return df


def _coerce_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _derive_team_win(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure team_win column exists (1/0)."""
    if "team_win" not in df.columns:
        if "team_points" in df.columns and "opponent_points" in df.columns:
            df["team_win"] = (df["team_points"] > df["opponent_points"]).astype(int)
            print("  Derived team_win from point totals.")
        else:
            df["team_win"] = pd.NA
    else:
        df["team_win"] = pd.to_numeric(df["team_win"], errors="coerce").fillna(0).astype(int)
    return df


def _fill_missing_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in REQUIRED_GAMES_COLUMNS:
        if col not in df.columns:
            print(f"  Adding missing column: {col}")
            df[col] = pd.NA
    return df


def _filter_d1(df: pd.DataFrame) -> pd.DataFrame:
    if "division" in df.columns:
        before = len(df)
        df = df[df["division"].astype(str).str.upper().isin(["D1", "1", "DIVISION I"])]
        print(f"  D1 filter: kept {len(df)} of {before} rows.")
    return df


def _drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    subset = [c for c in ["game_id", "team_id"] if c in df.columns]
    if subset:
        df = df.drop_duplicates(subset=subset)
    else:
        df = df.drop_duplicates()
    dropped = before - len(df)
    if dropped:
        print(f"  Removed {dropped} duplicate rows.")
    return df


def _handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    if "game_date" in df.columns:
        before = len(df)
        df = df.dropna(subset=["game_date"])
        dropped = before - len(df)
        if dropped:
            print(f"  Dropped {dropped} rows with missing game_date.")

    numeric_cols = ["team_points", "opponent_points"]
    for col in numeric_cols:
        if col in df.columns:
            median = df[col].median()
            filled = df[col].isna().sum()
            if filled:
                df[col] = df[col].fillna(median)
                print(f"  Filled {filled} missing {col} with median ({median:.1f}).")

    return df


def main() -> None:
    print(f"Reading raw games from: {RAW_GAMES_PATH}")
    if not RAW_GAMES_PATH.exists():
        print("ERROR: Raw games file not found. Place games.csv in data/raw/.")
        sys.exit(1)

    df = pd.read_csv(RAW_GAMES_PATH)
    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns.")

    df = _standardize_columns(df)
    df = _parse_dates(df)
    df = _coerce_numeric(df, [
        "team_points", "opponent_points", "team_win", "season",
        "fg_made", "fg_attempted", "three_made", "three_attempted",
        "ft_made", "ft_attempted", "blocks", "steals", "assists",
        "rebounds", "turnovers",
    ])
    df = _derive_team_win(df)
    df = _filter_d1(df)
    df = _drop_duplicates(df)
    df = _handle_missing_values(df)
    df = _fill_missing_columns(df)

    df = df.sort_values("game_date").reset_index(drop=True)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_GAMES_PATH, index=False)
    print(f"Saved {len(df)} cleaned rows to: {PROCESSED_GAMES_PATH}")
    print("Columns:", list(df.columns))


if __name__ == "__main__":
    main()
