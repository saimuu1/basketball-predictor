"""
build_dataset.py
Transforms cleaned historical games into feature rows for model training.

Each row represents a matchup from team_a's perspective. Only historical data
prior to the game date is used for features to prevent data leakage.

Usage (from backend/ directory):
    python -m app.scripts.build_dataset
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import (
    PROCESSED_GAMES_PATH,
    PROCESSED_DIR,
    MODEL_DATASET_PATH,
    RAW_COACHES_PATH,
    RAW_PLAYERS_PATH,
    RECENT_WINDOW_SHORT,
    RECENT_WINDOW_LONG,
    REQUIRED_COACHES_COLUMNS,
    REQUIRED_PLAYERS_COLUMNS,
)


# ---------------------------------------------------------------------------
# Lightweight feature helpers (mirror feature_builder logic but operate on
# a pre-filtered slice to avoid leakage)
# ---------------------------------------------------------------------------

def _team_recent(history: pd.DataFrame, team_id: str, n: int) -> pd.DataFrame:
    t = history[history["team_id"].astype(str) == str(team_id)]
    if "game_date" in t.columns:
        t = t.sort_values("game_date", ascending=False)
    return t.head(n)


def _safe_mean(series: pd.Series, default: float = 0.0) -> float:
    v = pd.to_numeric(series, errors="coerce")
    return float(v.mean()) if not v.isna().all() and len(v) > 0 else default


def _win_rate(recent: pd.DataFrame) -> float:
    if recent.empty:
        return 0.5
    return _safe_mean(recent["team_win"], 0.5)


def _avg_margin(recent: pd.DataFrame) -> float:
    if recent.empty:
        return 0.0
    pts = pd.to_numeric(recent["team_points"], errors="coerce")
    opp = pd.to_numeric(recent["opponent_points"], errors="coerce")
    m = pts - opp
    return float(m.mean()) if not m.isna().all() else 0.0


def _streak(recent: pd.DataFrame) -> tuple[int, int]:
    if recent.empty:
        return 0, 0
    wins = pd.to_numeric(recent["team_win"], errors="coerce").tolist()
    w, l = 0, 0
    for v in wins:
        if pd.isna(v):
            break
        if v == 1:
            if l > 0:
                break
            w += 1
        else:
            if w > 0:
                break
            l += 1
    return w, l


def _safe_pct(df: pd.DataFrame, made_col: str, att_col: str) -> float:
    made = pd.to_numeric(df[made_col], errors="coerce").sum() if made_col in df.columns else 0
    att = pd.to_numeric(df[att_col], errors="coerce").sum() if att_col in df.columns else 0
    return round(made / att, 4) if att > 0 else 0.0


def _safe_col_mean(df: pd.DataFrame, col: str) -> float:
    if col not in df.columns or df.empty:
        return 0.0
    v = pd.to_numeric(df[col], errors="coerce")
    return round(float(v.mean()), 2) if not v.isna().all() else 0.0


def _player_recent_logs(players_df: pd.DataFrame, team_id: str, before_date, n: int) -> pd.DataFrame:
    """Player logs for a team's most recent *n* game-dates before a cutoff."""
    team = players_df[players_df["team_id"].astype(str) == str(team_id)].copy()
    if team.empty:
        return team
    team["game_date"] = pd.to_datetime(team["game_date"], errors="coerce")
    team = team[team["game_date"] < before_date]
    if team.empty:
        return team
    recent_dates = team["game_date"].drop_duplicates().nlargest(n)
    return team[team["game_date"].isin(recent_dates)]


def _shooting_features(logs: pd.DataFrame) -> dict:
    if logs.empty:
        return {
            "fg_pct": 0.0, "three_pct": 0.0, "ft_pct": 0.0, "clutch_fg_pct": 0.0,
            "avg_blocks": 0.0, "avg_assists": 0.0, "avg_steals": 0.0,
            "avg_rebounds": 0.0, "avg_turnovers": 0.0,
        }
    return {
        "fg_pct": _safe_pct(logs, "fg_made", "fg_attempted"),
        "three_pct": _safe_pct(logs, "three_made", "three_attempted"),
        "ft_pct": _safe_pct(logs, "ft_made", "ft_attempted"),
        "clutch_fg_pct": _safe_pct(logs, "clutch_fg_made", "clutch_fg_attempted"),
        "avg_blocks": _safe_col_mean(logs, "blocks"),
        "avg_assists": _safe_col_mean(logs, "assists"),
        "avg_steals": _safe_col_mean(logs, "steals"),
        "avg_rebounds": _safe_col_mean(logs, "rebounds"),
        "avg_turnovers": _safe_col_mean(logs, "turnovers"),
    }


def _coach_win_pct(coaches_df: pd.DataFrame, team_id: str, season) -> float:
    if coaches_df.empty:
        return 0.5
    team = coaches_df[coaches_df["team_id"].astype(str) == str(team_id)]
    if team.empty:
        return 0.5
    if season is not None:
        exact = team[team["season"] == season]
        if not exact.empty:
            team = exact
        else:
            team = team.sort_values("season", ascending=False).head(1)
    else:
        team = team.sort_values("season", ascending=False).head(1)
    row = team.iloc[0]
    w = pd.to_numeric(row.get("wins", 0), errors="coerce") or 0
    l = pd.to_numeric(row.get("losses", 0), errors="coerce") or 0
    total = w + l
    return w / total if total > 0 else 0.5


def _coach_tourney_rate(coaches_df: pd.DataFrame, team_id: str) -> float:
    if coaches_df.empty:
        return 0.0
    team = coaches_df[coaches_df["team_id"].astype(str) == str(team_id)]
    if team.empty:
        return 0.0
    apps = pd.to_numeric(team["tournament_appearances"], errors="coerce").sum()
    seasons = len(team)
    return apps / seasons if seasons > 0 else 0.0


def _build_row_features(
    history: pd.DataFrame,
    team_a: str,
    team_b: str,
    home_team_id: str | None,
    players_df: pd.DataFrame,
    coaches_df: pd.DataFrame,
    game_date,
    season,
) -> dict:
    """Compute full matchup feature dict using only prior history."""
    a5 = _team_recent(history, team_a, RECENT_WINDOW_SHORT)
    a10 = _team_recent(history, team_a, RECENT_WINDOW_LONG)
    b5 = _team_recent(history, team_b, RECENT_WINDOW_SHORT)
    b10 = _team_recent(history, team_b, RECENT_WINDOW_LONG)

    a_wr5 = _win_rate(a5)
    a_wr10 = _win_rate(a10)
    b_wr5 = _win_rate(b5)
    b_wr10 = _win_rate(b10)

    a_mg5 = _avg_margin(a5)
    a_mg10 = _avg_margin(a10)
    b_mg5 = _avg_margin(b5)
    b_mg10 = _avg_margin(b10)

    a_scored5 = _safe_mean(a5["team_points"]) if not a5.empty else 0.0
    a_allowed5 = _safe_mean(a5["opponent_points"]) if not a5.empty else 0.0
    b_scored5 = _safe_mean(b5["team_points"]) if not b5.empty else 0.0
    b_allowed5 = _safe_mean(b5["opponent_points"]) if not b5.empty else 0.0

    a_ws, a_ls = _streak(a5)
    b_ws, b_ls = _streak(b5)

    if home_team_id is not None:
        htid = str(home_team_id)
        if htid == str(team_a):
            hc = 1.0
        elif htid == str(team_b):
            hc = -1.0
        else:
            hc = 0.0
    else:
        hc = 0.0

    # Player / shooting / defense features
    a_logs = _player_recent_logs(players_df, team_a, game_date, RECENT_WINDOW_SHORT)
    b_logs = _player_recent_logs(players_df, team_b, game_date, RECENT_WINDOW_SHORT)
    a_sh = _shooting_features(a_logs)
    b_sh = _shooting_features(b_logs)

    # Coach features
    a_cwp = _coach_win_pct(coaches_df, team_a, season)
    b_cwp = _coach_win_pct(coaches_df, team_b, season)
    a_ctr = _coach_tourney_rate(coaches_df, team_a)
    b_ctr = _coach_tourney_rate(coaches_df, team_b)

    return {
        # Team form diffs
        "diff_win_rate_5": a_wr5 - b_wr5,
        "diff_win_rate_10": a_wr10 - b_wr10,
        "diff_avg_margin_5": a_mg5 - b_mg5,
        "diff_avg_margin_10": a_mg10 - b_mg10,
        "diff_avg_scored_5": a_scored5 - b_scored5,
        "diff_avg_allowed_5": a_allowed5 - b_allowed5,
        "diff_win_streak": float(a_ws - b_ws),
        "diff_loss_streak": float(a_ls - b_ls),
        # Player trends (hot-player logic deferred to runtime for speed)
        "diff_hot_players": 0.0,
        "diff_player_trend": 0.0,
        # Shooting diffs
        "diff_fg_pct": a_sh["fg_pct"] - b_sh["fg_pct"],
        "diff_three_pct": a_sh["three_pct"] - b_sh["three_pct"],
        "diff_ft_pct": a_sh["ft_pct"] - b_sh["ft_pct"],
        "diff_clutch_fg_pct": a_sh["clutch_fg_pct"] - b_sh["clutch_fg_pct"],
        # Defense / playmaking diffs
        "diff_blocks": a_sh["avg_blocks"] - b_sh["avg_blocks"],
        "diff_assists": a_sh["avg_assists"] - b_sh["avg_assists"],
        "diff_steals": a_sh["avg_steals"] - b_sh["avg_steals"],
        "diff_rebounds": a_sh["avg_rebounds"] - b_sh["avg_rebounds"],
        "diff_turnovers": a_sh["avg_turnovers"] - b_sh["avg_turnovers"],
        # Coach diffs
        "diff_coach_win_pct": a_cwp - b_cwp,
        "diff_coach_tourney_rate": a_ctr - b_ctr,
        # Venue
        "home_court_advantage": hc,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _load_optional_csv(path, required_cols: list[str]) -> pd.DataFrame:
    """Load a CSV if it exists; return empty DataFrame otherwise."""
    if not path.exists():
        print(f"  Optional file not found: {path} — features will default to 0.")
        return pd.DataFrame(columns=required_cols)
    try:
        df = pd.read_csv(path)
        for col in required_cols:
            if col not in df.columns:
                df[col] = pd.NA
        return df
    except Exception as exc:
        print(f"  Failed to read {path}: {exc}")
        return pd.DataFrame(columns=required_cols)


def main() -> None:
    print(f"Loading cleaned games from: {PROCESSED_GAMES_PATH}")
    if not PROCESSED_GAMES_PATH.exists():
        print("ERROR: Cleaned games not found. Run `python -m scripts.clean_data` first.")
        sys.exit(1)

    games = pd.read_csv(PROCESSED_GAMES_PATH)
    games["game_date"] = pd.to_datetime(games["game_date"], errors="coerce")
    games = games.dropna(subset=["game_date"]).sort_values("game_date").reset_index(drop=True)
    print(f"  {len(games)} game rows loaded.")

    players_df = _load_optional_csv(RAW_PLAYERS_PATH, REQUIRED_PLAYERS_COLUMNS)
    if "game_date" in players_df.columns:
        players_df["game_date"] = pd.to_datetime(players_df["game_date"], errors="coerce")
    print(f"  {len(players_df)} player log rows loaded.")

    coaches_df = _load_optional_csv(RAW_COACHES_PATH, REQUIRED_COACHES_COLUMNS)
    print(f"  {len(coaches_df)} coach rows loaded.")

    seen_game_ids: set[str] = set()
    rows: list[dict] = []

    for idx, row in games.iterrows():
        gid = str(row.get("game_id", idx))
        if gid in seen_game_ids:
            continue
        seen_game_ids.add(gid)

        team_a = str(row["team_id"])
        team_b = str(row["opponent_id"])
        game_date = row["game_date"]
        season = row.get("season", None)

        history = games[games["game_date"] < game_date]
        if len(history) < RECENT_WINDOW_SHORT:
            continue

        home_team_id = None
        if "home_away" in games.columns:
            ha = str(row.get("home_away", "")).upper()
            if ha in ("H", "HOME"):
                home_team_id = team_a
            elif ha in ("A", "AWAY"):
                home_team_id = team_b

        feats = _build_row_features(
            history, team_a, team_b, home_team_id,
            players_df=players_df,
            coaches_df=coaches_df,
            game_date=game_date,
            season=season,
        )
        feats["team_a_win"] = int(row.get("team_win", 0))
        rows.append(feats)

        if len(rows) % 500 == 0:
            print(f"  Processed {len(rows)} matchups...")

    if not rows:
        print("ERROR: No training rows generated. Check your data.")
        sys.exit(1)

    dataset = pd.DataFrame(rows)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(MODEL_DATASET_PATH, index=False)

    print(f"\nDataset saved to: {MODEL_DATASET_PATH}")
    print(f"  Total rows: {len(dataset)}")
    print(f"  Columns: {list(dataset.columns)}")
    print(f"  Win rate: {dataset['team_a_win'].mean():.3f}")


if __name__ == "__main__":
    main()
