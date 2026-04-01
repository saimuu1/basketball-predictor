"""
Persistent SQLite storage for completed games.

Database lives at  backend/data/games.db  and is created automatically on
first startup. All completed games seen by the app are upserted here so they
remain accessible after the ESPN API stops serving them.
"""
from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator

logger = logging.getLogger(__name__)

_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "games.db"

_CREATE_GAMES_TABLE = """
CREATE TABLE IF NOT EXISTS games (
    game_id       TEXT PRIMARY KEY,
    game_date     TEXT NOT NULL,
    season        INTEGER NOT NULL,
    team_a_id     TEXT NOT NULL,
    team_b_id     TEXT NOT NULL,
    team_a_name   TEXT NOT NULL,
    team_b_name   TEXT NOT NULL,
    home_team_id  TEXT,
    team_a_score  INTEGER,
    team_b_score  INTEGER,
    team_a_logo   TEXT,
    team_b_logo   TEXT,
    status        TEXT,
    stored_at     TEXT NOT NULL
);
"""

_CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_games_team_names
    ON games (team_a_name, team_b_name);
"""


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

@contextmanager
def _connect() -> Generator[sqlite3.Connection, None, None]:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create tables if they don't exist. Safe to call multiple times."""
    with _connect() as conn:
        conn.execute(_CREATE_GAMES_TABLE)
        conn.execute(_CREATE_INDEX)
    logger.info("Database initialised at %s", _DB_PATH)


# ---------------------------------------------------------------------------
# Season helper
# ---------------------------------------------------------------------------

def _season_for_date(date_str: str) -> int:
    """
    College basketball seasons span two calendar years.
    A game played Sep-Dec belongs to the *following* calendar year's season.
    A game played Jan-Aug belongs to the *current* calendar year's season.
    E.g. Nov 2025 -> 2026,  Mar 2026 -> 2026.
    """
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.year + 1 if dt.month >= 9 else dt.year
    except Exception:
        return datetime.utcnow().year


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def store_games(games: list[dict]) -> int:
    """
    Upsert a list of completed game dicts into the database.
    Only games that have score data (team_a_score is not None) are stored.
    Returns the number of rows inserted/updated.
    """
    if not games:
        return 0

    now = datetime.utcnow().isoformat()
    count = 0

    with _connect() as conn:
        for g in games:
            # Only persist games that have scores (completed games)
            if g.get("team_a_score") is None and g.get("team_b_score") is None:
                continue
            try:
                conn.execute(
                    """
                    INSERT INTO games
                        (game_id, game_date, season, team_a_id, team_b_id,
                         team_a_name, team_b_name, home_team_id,
                         team_a_score, team_b_score,
                         team_a_logo, team_b_logo, status, stored_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(game_id) DO UPDATE SET
                        team_a_score = excluded.team_a_score,
                        team_b_score = excluded.team_b_score,
                        team_a_logo  = excluded.team_a_logo,
                        team_b_logo  = excluded.team_b_logo,
                        status       = excluded.status,
                        stored_at    = excluded.stored_at
                    """,
                    (
                        g["game_id"],
                        g.get("game_date", ""),
                        _season_for_date(g.get("game_date", "")),
                        g.get("team_a_id", ""),
                        g.get("team_b_id", ""),
                        g.get("team_a_name", "TBD"),
                        g.get("team_b_name", "TBD"),
                        g.get("home_team_id"),
                        g.get("team_a_score"),
                        g.get("team_b_score"),
                        g.get("team_a_logo"),
                        g.get("team_b_logo"),
                        g.get("status", "Final"),
                        now,
                    ),
                )
                count += 1
            except Exception as exc:
                logger.warning("Failed to store game %s: %s", g.get("game_id"), exc)

    logger.debug("Stored/updated %d game(s) in database", count)
    return count


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def get_recent_games(days: int = 14) -> list[dict]:
    """Return completed games from the last *days* calendar days."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM games
            WHERE game_date >= datetime('now', ? || ' days')
            ORDER BY game_date DESC
            """,
            (f"-{days}",),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def search_games(team_name: str, season: int | None = None) -> list[dict]:
    """
    Search completed games by team name (case-insensitive partial match).
    Optionally filter to a specific season year.
    """
    pattern = f"%{team_name}%"
    with _connect() as conn:
        if season:
            rows = conn.execute(
                """
                SELECT * FROM games
                WHERE (team_a_name LIKE ? OR team_b_name LIKE ?)
                  AND season = ?
                ORDER BY game_date DESC
                """,
                (pattern, pattern, season),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM games
                WHERE team_a_name LIKE ? OR team_b_name LIKE ?
                ORDER BY game_date DESC
                """,
                (pattern, pattern),
            ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_game_count() -> int:
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]


def get_season_game_count(season: int) -> int:
    """Return how many games are stored for a given season year."""
    with _connect() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM games WHERE season = ?", (season,)
        ).fetchone()[0]
