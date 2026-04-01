from __future__ import annotations

import numpy as np
import pandas as pd

from app.core.config import RECENT_WINDOW_SHORT, RECENT_WINDOW_LONG


# ---------------------------------------------------------------------------
# Team-form helpers
# ---------------------------------------------------------------------------

def _team_recent_games(games_df: pd.DataFrame, team_id: str, n: int) -> pd.DataFrame:
    """Return the most recent *n* games for a team, sorted newest-first."""
    team_games = games_df[games_df["team_id"].astype(str) == str(team_id)].copy()
    if "game_date" in team_games.columns:
        team_games = team_games.sort_values("game_date", ascending=False)
    return team_games.head(n)


def _win_rate(recent: pd.DataFrame) -> float:
    if recent.empty:
        return 0.5
    wins = pd.to_numeric(recent["team_win"], errors="coerce")
    return float(wins.mean()) if not wins.isna().all() else 0.5


def _avg_margin(recent: pd.DataFrame) -> float:
    if recent.empty:
        return 0.0
    pts = pd.to_numeric(recent["team_points"], errors="coerce")
    opp = pd.to_numeric(recent["opponent_points"], errors="coerce")
    margins = pts - opp
    return float(margins.mean()) if not margins.isna().all() else 0.0


def _avg_points_scored(recent: pd.DataFrame) -> float:
    if recent.empty:
        return 0.0
    pts = pd.to_numeric(recent["team_points"], errors="coerce")
    return float(pts.mean()) if not pts.isna().all() else 0.0


def _avg_points_allowed(recent: pd.DataFrame) -> float:
    if recent.empty:
        return 0.0
    opp = pd.to_numeric(recent["opponent_points"], errors="coerce")
    return float(opp.mean()) if not opp.isna().all() else 0.0


def _current_streak(recent: pd.DataFrame) -> tuple[int, int]:
    """Return (win_streak, loss_streak) from most-recent games outward."""
    if recent.empty:
        return 0, 0
    wins = pd.to_numeric(recent["team_win"], errors="coerce").tolist()
    win_streak = 0
    loss_streak = 0
    for w in wins:
        if pd.isna(w):
            break
        if w == 1:
            if loss_streak > 0:
                break
            win_streak += 1
        else:
            if win_streak > 0:
                break
            loss_streak += 1
    return win_streak, loss_streak


def compute_team_features(games_df: pd.DataFrame, team_id: str) -> dict:
    short = _team_recent_games(games_df, team_id, RECENT_WINDOW_SHORT)
    long = _team_recent_games(games_df, team_id, RECENT_WINDOW_LONG)

    win_streak, loss_streak = _current_streak(short)

    return {
        "wins_last_5": float(pd.to_numeric(short["team_win"], errors="coerce").sum()) if not short.empty else 0.0,
        "wins_last_10": float(pd.to_numeric(long["team_win"], errors="coerce").sum()) if not long.empty else 0.0,
        "win_rate_last_5": _win_rate(short),
        "win_rate_last_10": _win_rate(long),
        "avg_margin_last_5": _avg_margin(short),
        "avg_margin_last_10": _avg_margin(long),
        "avg_points_scored_last_5": _avg_points_scored(short),
        "avg_points_allowed_last_5": _avg_points_allowed(short),
        "win_streak": float(win_streak),
        "loss_streak": float(loss_streak),
    }


# ---------------------------------------------------------------------------
# Coach helpers
# ---------------------------------------------------------------------------

def compute_coach_features(coaches_df: pd.DataFrame, team_id: str) -> dict:
    defaults = {"coach_win_pct": 0.5, "coach_tourney_rate": 0.0}
    if coaches_df.empty:
        return defaults

    team_coaches = coaches_df[coaches_df["team_id"].astype(str) == str(team_id)]
    if team_coaches.empty:
        return defaults

    latest = team_coaches.sort_values("season", ascending=False).iloc[0]
    wins = pd.to_numeric(latest.get("wins", 0), errors="coerce") or 0
    losses = pd.to_numeric(latest.get("losses", 0), errors="coerce") or 0
    total = wins + losses
    win_pct = wins / total if total > 0 else 0.5

    tourney_apps = pd.to_numeric(team_coaches["tournament_appearances"], errors="coerce").sum()
    seasons = len(team_coaches)
    tourney_rate = tourney_apps / seasons if seasons > 0 else 0.0

    return {
        "coach_win_pct": round(float(win_pct), 4),
        "coach_tourney_rate": round(float(tourney_rate), 4),
    }


# ---------------------------------------------------------------------------
# Player-streak helpers
# ---------------------------------------------------------------------------

def _player_season_avg(players_df: pd.DataFrame, team_id: str) -> float:
    team_players = players_df[players_df["team_id"].astype(str) == str(team_id)]
    pts = pd.to_numeric(team_players["points"], errors="coerce")
    return float(pts.mean()) if not pts.isna().all() and not team_players.empty else 0.0


def _player_recent_avg(players_df: pd.DataFrame, team_id: str, n: int) -> float:
    team_players = players_df[players_df["team_id"].astype(str) == str(team_id)].copy()
    if team_players.empty:
        return 0.0
    if "game_date" in team_players.columns:
        team_players["game_date"] = pd.to_datetime(team_players["game_date"], errors="coerce")
        recent_dates = team_players["game_date"].drop_duplicates().nlargest(n)
        team_players = team_players[team_players["game_date"].isin(recent_dates)]
    pts = pd.to_numeric(team_players["points"], errors="coerce")
    return float(pts.mean()) if not pts.isna().all() else 0.0


def _hot_players_count(players_df: pd.DataFrame, team_id: str, n: int = RECENT_WINDOW_SHORT) -> float:
    team_players = players_df[players_df["team_id"].astype(str) == str(team_id)].copy()
    if team_players.empty or "player_id" not in team_players.columns:
        return 0.0

    if "game_date" in team_players.columns:
        team_players["game_date"] = pd.to_datetime(team_players["game_date"], errors="coerce")

    hot = 0
    for pid, grp in team_players.groupby("player_id"):
        season_avg = pd.to_numeric(grp["points"], errors="coerce").mean()
        if pd.isna(season_avg) or season_avg == 0:
            continue
        if "game_date" in grp.columns:
            recent = grp.sort_values("game_date", ascending=False).head(n)
        else:
            recent = grp.tail(n)
        recent_avg = pd.to_numeric(recent["points"], errors="coerce").mean()
        if not pd.isna(recent_avg) and recent_avg > season_avg:
            hot += 1
    return float(hot)


def compute_player_features(players_df: pd.DataFrame, team_id: str) -> dict:
    if players_df.empty:
        return {
            "hot_players_count": 0.0,
            "player_points_trend": 0.0,
        }

    season_avg = _player_season_avg(players_df, team_id)
    recent_avg = _player_recent_avg(players_df, team_id, RECENT_WINDOW_SHORT)
    trend = recent_avg - season_avg if season_avg > 0 else 0.0

    return {
        "hot_players_count": _hot_players_count(players_df, team_id),
        "player_points_trend": round(trend, 2),
    }


# ---------------------------------------------------------------------------
# Shooting / defense / box-score helpers
# ---------------------------------------------------------------------------

def _get_recent_player_logs(players_df: pd.DataFrame, team_id: str, n: int) -> pd.DataFrame:
    """Return player logs for a team's most recent *n* game dates."""
    team = players_df[players_df["team_id"].astype(str) == str(team_id)].copy()
    if team.empty:
        return team
    if "game_date" in team.columns:
        team["game_date"] = pd.to_datetime(team["game_date"], errors="coerce")
        recent_dates = team["game_date"].drop_duplicates().nlargest(n)
        team = team[team["game_date"].isin(recent_dates)]
    return team


def _safe_pct(df: pd.DataFrame, made_col: str, att_col: str) -> float:
    made = pd.to_numeric(df[made_col], errors="coerce").sum() if made_col in df.columns else 0
    att = pd.to_numeric(df[att_col], errors="coerce").sum() if att_col in df.columns else 0
    return round(made / att, 4) if att > 0 else 0.0


def _safe_col_mean(df: pd.DataFrame, col: str) -> float:
    if col not in df.columns or df.empty:
        return 0.0
    v = pd.to_numeric(df[col], errors="coerce")
    return round(float(v.mean()), 2) if not v.isna().all() else 0.0


def compute_shooting_features(players_df: pd.DataFrame, team_id: str, n: int = RECENT_WINDOW_SHORT) -> dict:
    defaults = {
        "fg_pct": 0.0, "three_pct": 0.0, "ft_pct": 0.0,
        "clutch_fg_pct": 0.0,
        "avg_blocks": 0.0, "avg_assists": 0.0, "avg_steals": 0.0,
        "avg_rebounds": 0.0, "avg_turnovers": 0.0,
    }
    if players_df.empty:
        return defaults

    recent = _get_recent_player_logs(players_df, team_id, n)
    if recent.empty:
        return defaults

    return {
        "fg_pct": _safe_pct(recent, "fg_made", "fg_attempted"),
        "three_pct": _safe_pct(recent, "three_made", "three_attempted"),
        "ft_pct": _safe_pct(recent, "ft_made", "ft_attempted"),
        "clutch_fg_pct": _safe_pct(recent, "clutch_fg_made", "clutch_fg_attempted"),
        "avg_blocks": _safe_col_mean(recent, "blocks"),
        "avg_assists": _safe_col_mean(recent, "assists"),
        "avg_steals": _safe_col_mean(recent, "steals"),
        "avg_rebounds": _safe_col_mean(recent, "rebounds"),
        "avg_turnovers": _safe_col_mean(recent, "turnovers"),
    }


# ---------------------------------------------------------------------------
# Matchup features (Team A vs Team B)
# ---------------------------------------------------------------------------

def build_matchup_features(
    team_a_id: str,
    team_b_id: str,
    home_team_id: str | None,
    games_df: pd.DataFrame,
    players_df: pd.DataFrame,
    coaches_df: pd.DataFrame | None = None,
    torvik_stats_a: dict | None = None,
    torvik_stats_b: dict | None = None,
    espn_record_a: dict | None = None,
    espn_record_b: dict | None = None,
    espn_stats_a: dict | None = None,
    espn_stats_b: dict | None = None,
    seed_a: float | None = None,
    seed_b: float | None = None,
) -> dict:
    # --- Local CSV form (momentum / historical baseline) ---
    a_team = compute_team_features(games_df, team_a_id)
    b_team = compute_team_features(games_df, team_b_id)
    a_player = compute_player_features(players_df, team_a_id)
    b_player = compute_player_features(players_df, team_b_id)

    # Shooting: prefer live Barttorvik, else fall back to local CSV
    a_shoot = torvik_stats_a if torvik_stats_a is not None else compute_shooting_features(players_df, team_a_id)
    b_shoot = torvik_stats_b if torvik_stats_b is not None else compute_shooting_features(players_df, team_b_id)

    _coaches = coaches_df if coaches_df is not None else pd.DataFrame()
    a_coach = compute_coach_features(_coaches, team_a_id)
    b_coach = compute_coach_features(_coaches, team_b_id)

    # Home court
    if home_team_id is not None:
        htid = str(home_team_id)
        if htid == str(team_a_id):
            home_court = 1.0
        elif htid == str(team_b_id):
            home_court = -1.0
        else:
            home_court = 0.0
    else:
        home_court = 0.0

    # --- Store all raw values for factor descriptions ---
    features: dict = {}

    for key, val in a_team.items():
        features[f"a_{key}"] = val
    for key, val in b_team.items():
        features[f"b_{key}"] = val
    for key, val in a_player.items():
        features[f"a_{key}"] = val
    for key, val in b_player.items():
        features[f"b_{key}"] = val
    for key, val in a_shoot.items():
        features[f"a_{key}"] = val
    for key, val in b_shoot.items():
        features[f"b_{key}"] = val
    for key, val in a_coach.items():
        features[f"a_{key}"] = val
    for key, val in b_coach.items():
        features[f"b_{key}"] = val

    # Store ESPN season data
    _era = espn_record_a or {}
    _erb = espn_record_b or {}
    _esa = espn_stats_a or {}
    _esb = espn_stats_b or {}
    for key, val in _era.items():
        features[f"a_espn_{key}"] = val
    for key, val in _erb.items():
        features[f"b_espn_{key}"] = val
    for key, val in _esa.items():
        features[f"a_espn_stats_{key}"] = val
    for key, val in _esb.items():
        features[f"b_espn_stats_{key}"] = val

    features["home_court_advantage"] = home_court

    # =========================================================================
    # DIFFERENCE FEATURES (positive = Team A advantage)
    # =========================================================================

    # --- Team form (CSV / local) ---
    features["diff_win_rate_5"] = a_team["win_rate_last_5"] - b_team["win_rate_last_5"]
    features["diff_win_rate_10"] = a_team["win_rate_last_10"] - b_team["win_rate_last_10"]
    features["diff_avg_margin_5"] = a_team["avg_margin_last_5"] - b_team["avg_margin_last_5"]
    features["diff_avg_margin_10"] = a_team["avg_margin_last_10"] - b_team["avg_margin_last_10"]
    features["diff_avg_scored_5"] = a_team["avg_points_scored_last_5"] - b_team["avg_points_scored_last_5"]
    features["diff_avg_allowed_5"] = a_team["avg_points_allowed_last_5"] - b_team["avg_points_allowed_last_5"]
    features["diff_win_streak"] = a_team["win_streak"] - b_team["win_streak"]
    features["diff_loss_streak"] = a_team["loss_streak"] - b_team["loss_streak"]

    # --- Player trends (CSV) ---
    features["diff_hot_players"] = a_player["hot_players_count"] - b_player["hot_players_count"]
    features["diff_player_trend"] = a_player["player_points_trend"] - b_player["player_points_trend"]

    # --- Shooting (Barttorvik or CSV) ---
    features["diff_fg_pct"] = a_shoot.get("fg_pct", 0.45) - b_shoot.get("fg_pct", 0.45)
    features["diff_efg_pct"] = features["diff_fg_pct"]  # fg_pct is eFG from Torvik
    features["diff_three_pct"] = a_shoot.get("three_pct", 0.33) - b_shoot.get("three_pct", 0.33)
    features["diff_ft_pct"] = a_shoot.get("ft_pct", 0.70) - b_shoot.get("ft_pct", 0.70)
    features["diff_two_pct"] = a_shoot.get("two_pct", 0.50) - b_shoot.get("two_pct", 0.50)
    features["diff_ts_pct"] = a_shoot.get("ts_pct", 0.53) - b_shoot.get("ts_pct", 0.53)
    features["diff_clutch_fg_pct"] = a_shoot.get("clutch_fg_pct", 0.45) - b_shoot.get("clutch_fg_pct", 0.45)
    features["diff_three_rate"] = a_shoot.get("three_rate", 0.38) - b_shoot.get("three_rate", 0.38)
    features["diff_ft_rate"] = a_shoot.get("ft_rate", 0.29) - b_shoot.get("ft_rate", 0.29)

    # --- Defense / playmaking (Barttorvik or CSV) ---
    features["diff_blocks"] = a_shoot.get("avg_blocks", 0.0) - b_shoot.get("avg_blocks", 0.0)
    features["diff_assists"] = a_shoot.get("avg_assists", 0.0) - b_shoot.get("avg_assists", 0.0)
    features["diff_steals"] = a_shoot.get("avg_steals", 0.0) - b_shoot.get("avg_steals", 0.0)
    features["diff_rebounds"] = a_shoot.get("avg_rebounds", 0.0) - b_shoot.get("avg_rebounds", 0.0)
    features["diff_turnovers"] = a_shoot.get("avg_turnovers", 0.0) - b_shoot.get("avg_turnovers", 0.0)
    features["diff_blk_pct"] = a_shoot.get("blk_pct", 0.0) - b_shoot.get("blk_pct", 0.0)
    features["diff_stl_pct"] = a_shoot.get("stl_pct", 0.0) - b_shoot.get("stl_pct", 0.0)
    features["diff_orb_pct"] = a_shoot.get("orb_pct", 0.0) - b_shoot.get("orb_pct", 0.0)
    features["diff_drb_pct"] = a_shoot.get("drb_pct", 0.0) - b_shoot.get("drb_pct", 0.0)
    features["diff_ast_pct"] = a_shoot.get("ast_pct", 0.0) - b_shoot.get("ast_pct", 0.0)
    features["diff_tov_pct"] = a_shoot.get("tov_pct", 0.0) - b_shoot.get("tov_pct", 0.0)

    # --- Roster / experience (Barttorvik) ---
    features["diff_experience"] = a_shoot.get("avg_experience", 2.0) - b_shoot.get("avg_experience", 2.0)
    features["diff_rotation_size"] = a_shoot.get("rotation_size", 8.0) - b_shoot.get("rotation_size", 8.0)
    # Usage concentration: lower is better (balanced team), so negate for A advantage
    features["diff_usage_concentration"] = b_shoot.get("usage_concentration", 1.0) - a_shoot.get("usage_concentration", 1.0)

    # --- Coach (CSV) ---
    features["diff_coach_win_pct"] = a_coach["coach_win_pct"] - b_coach["coach_win_pct"]
    features["diff_coach_tourney_rate"] = a_coach["coach_tourney_rate"] - b_coach["coach_tourney_rate"]

    # --- ESPN season-level record ---
    features["diff_win_pct"] = _era.get("win_pct", 0.5) - _erb.get("win_pct", 0.5)
    features["diff_conf_win_pct"] = _era.get("conf_win_pct", 0.5) - _erb.get("conf_win_pct", 0.5)
    features["diff_ppg"] = _era.get("ppg", 70.0) - _erb.get("ppg", 70.0)
    features["diff_oppg"] = _erb.get("oppg", 70.0) - _era.get("oppg", 70.0)  # lower is better on defense
    features["diff_point_diff"] = _era.get("point_differential", 0.0) - _erb.get("point_differential", 0.0)
    features["diff_streak"] = _era.get("streak", 0.0) - _erb.get("streak", 0.0)
    # Rank: lower number is better, so negate
    features["diff_rank"] = _erb.get("rank", 99.0) - _era.get("rank", 99.0)

    # --- ESPN season-level box stats ---
    features["diff_bpg"] = _esa.get("bpg", 0.0) - _esb.get("bpg", 0.0)
    features["diff_spg"] = _esa.get("spg", 0.0) - _esb.get("spg", 0.0)
    features["diff_rpg"] = _esa.get("rpg", 0.0) - _esb.get("rpg", 0.0)
    features["diff_orpg"] = _esa.get("orpg", 0.0) - _esb.get("orpg", 0.0)
    features["diff_drpg"] = _esa.get("drpg", 0.0) - _esb.get("drpg", 0.0)
    features["diff_apg"] = _esa.get("apg", 0.0) - _esb.get("apg", 0.0)
    features["diff_topg"] = _esb.get("topg", 0.0) - _esa.get("topg", 0.0)  # fewer TOs = better
    features["diff_ast_to_ratio"] = _esa.get("ast_to_ratio", 1.0) - _esb.get("ast_to_ratio", 1.0)
    features["diff_fouls_pg"] = _esb.get("fouls_pg", 17.0) - _esa.get("fouls_pg", 17.0)  # fewer fouls = better
    features["diff_scoring_eff"] = _esa.get("scoring_efficiency", 1.2) - _esb.get("scoring_efficiency", 1.2)
    features["diff_shooting_eff"] = _esa.get("shooting_efficiency", 0.5) - _esb.get("shooting_efficiency", 0.5)

    # Merge shooting: if ESPN has FG%/3PT%/FT%, fill in only when Torvik not available
    if torvik_stats_a is None and _esa:
        features["diff_fg_pct"] = _esa.get("fg_pct", 0.45) - _esb.get("fg_pct", 0.45)
        features["diff_three_pct"] = _esa.get("three_pct", 0.33) - _esb.get("three_pct", 0.33)
        features["diff_ft_pct"] = _esa.get("ft_pct", 0.70) - _esb.get("ft_pct", 0.70)

    # --- Tournament context ---
    s_a = float(seed_a) if seed_a is not None else 8.0
    s_b = float(seed_b) if seed_b is not None else 8.0
    features["diff_seed"] = s_b - s_a   # lower seed number = better team, so positive = A is better seed
    features["a_seed"] = s_a
    features["b_seed"] = s_b
    features["is_tournament"] = 1.0
    features["neutral_site"] = 1.0 if home_court == 0.0 else 0.0

    return features


# ---------------------------------------------------------------------------
# Explanation / factors
# ---------------------------------------------------------------------------

def _impact_label(diff: float) -> str:
    if diff > 0.01:
        return "team_a"
    elif diff < -0.01:
        return "team_b"
    return "neutral"


def build_feature_factors(
    features: dict,
    team_a_name: str,
    team_b_name: str,
) -> list[dict]:
    """
    Build frontend-friendly factor dicts from computed features.
    Non-neutral factors are returned first (sorted by magnitude).
    Neutral factors are appended at the end.
    """

    def _favored(diff: float) -> str:
        if diff > 0.01:
            return team_a_name
        elif diff < -0.01:
            return team_b_name
        return "Even"

    def _f(key: str) -> float:
        return features.get(key, 0.0)

    raw: list[dict] = []

    # --- Season record (ESPN) ---
    wp = _f("diff_win_pct")
    raw.append({"name": "Season Win %", "value": round(wp, 3), "impact": _impact_label(wp),
        "description": f"{_favored(wp)} has the better season record "
                       f"({_f('a_espn_win_pct'):.1%} vs {_f('b_espn_win_pct'):.1%})."})

    pd_diff = _f("diff_point_diff")
    raw.append({"name": "Point Differential", "value": round(pd_diff, 1), "impact": _impact_label(pd_diff),
        "description": f"{_favored(pd_diff)} is winning games by a bigger margin on average "
                       f"({_f('a_espn_point_differential'):+.1f} vs {_f('b_espn_point_differential'):+.1f} pts/game)."})

    ppg = _f("diff_ppg")
    raw.append({"name": "Scoring Offense", "value": round(ppg, 1), "impact": _impact_label(ppg),
        "description": f"{_favored(ppg)} is putting up more points per game "
                       f"({_f('a_espn_ppg'):.1f} vs {_f('b_espn_ppg'):.1f} PPG)."})

    oppg = _f("diff_oppg")
    raw.append({"name": "Scoring Defense", "value": round(oppg, 1), "impact": _impact_label(oppg),
        "description": f"{_favored(oppg)} is giving up fewer points per game "
                       f"({_f('a_espn_oppg'):.1f} vs {_f('b_espn_oppg'):.1f} OPPG)."})

    rnk = _f("diff_rank")
    if abs(rnk) > 2:
        raw.append({"name": "National Ranking", "value": round(rnk, 0), "impact": _impact_label(rnk),
            "description": f"{_favored(rnk)} is ranked higher nationally — that's not just noise."})

    streak = _f("diff_streak")
    raw.append({"name": "Current Streak", "value": round(streak, 0), "impact": _impact_label(streak),
        "description": f"{_favored(streak)} is carrying better momentum into this game "
                       f"(streak: {_f('a_espn_streak'):+.0f} vs {_f('b_espn_streak'):+.0f})."})

    # --- Shooting ---
    fg = _f("diff_fg_pct")
    raw.append({"name": "Effective FG%", "value": round(fg, 4), "impact": _impact_label(fg),
        "description": f"{_favored(fg)} is the more efficient shooting team this season "
                       f"({_f('a_fg_pct'):.1%} vs {_f('b_fg_pct'):.1%} eFG%)."})

    ts = _f("diff_ts_pct")
    raw.append({"name": "True Shooting %", "value": round(ts, 4), "impact": _impact_label(ts),
        "description": f"{_favored(ts)} gets more value out of every shot attempt including FTs "
                       f"({_f('a_ts_pct'):.1%} vs {_f('b_ts_pct'):.1%} TS%)."})

    tp = _f("diff_three_pct")
    raw.append({"name": "3-Point %", "value": round(tp, 4), "impact": _impact_label(tp),
        "description": f"{_favored(tp)} is connecting from deep at a better rate "
                       f"({_f('a_three_pct'):.1%} vs {_f('b_three_pct'):.1%})."})

    tpr = _f("diff_three_rate")
    raw.append({"name": "3-Point Attempt Rate", "value": round(tpr, 3), "impact": _impact_label(tpr),
        "description": f"{_favored(tpr)} leans heavier on the three-ball "
                       f"({_f('a_three_rate'):.1%} vs {_f('b_three_rate'):.1%} of FGA)."})

    ft = _f("diff_ft_pct")
    raw.append({"name": "Free Throw %", "value": round(ft, 4), "impact": _impact_label(ft),
        "description": f"{_favored(ft)} is more automatic from the stripe "
                       f"({_f('a_ft_pct'):.1%} vs {_f('b_ft_pct'):.1%} FT%)."})

    ftr = _f("diff_ft_rate")
    raw.append({"name": "Free Throw Rate", "value": round(ftr, 3), "impact": _impact_label(ftr),
        "description": f"{_favored(ftr)} draws fouls at a higher rate, getting to the line more "
                       f"({_f('a_ft_rate'):.1%} vs {_f('b_ft_rate'):.1%} FTA/FGA)."})

    two = _f("diff_two_pct")
    raw.append({"name": "2-Point %", "value": round(two, 4), "impact": _impact_label(two),
        "description": f"{_favored(two)} is more efficient around the basket and in the mid-range "
                       f"({_f('a_two_pct'):.1%} vs {_f('b_two_pct'):.1%})."})

    cfg = _f("diff_clutch_fg_pct")
    raw.append({"name": "Clutch Shooting", "value": round(cfg, 4), "impact": _impact_label(cfg),
        "description": f"{_favored(cfg)} steps up when the game is on the line — better clutch efficiency this season."})

    se = _f("diff_scoring_eff")
    raw.append({"name": "Scoring Efficiency", "value": round(se, 4), "impact": _impact_label(se),
        "description": f"{_favored(se)} scores more points per possession attempt "
                       f"({_f('a_espn_stats_scoring_efficiency'):.3f} vs {_f('b_espn_stats_scoring_efficiency'):.3f})."})

    # --- Defense ---
    bpg = _f("diff_bpg")
    raw.append({"name": "Blocks per Game", "value": round(bpg, 2), "impact": _impact_label(bpg),
        "description": f"{_favored(bpg)} is the tougher team to finish against at the rim "
                       f"({_f('a_espn_stats_bpg'):.1f} vs {_f('b_espn_stats_bpg'):.1f} BPG)."})

    blk_pct = _f("diff_blk_pct")
    raw.append({"name": "Block Rate", "value": round(blk_pct, 3), "impact": _impact_label(blk_pct),
        "description": f"{_favored(blk_pct)} contests more shots relative to opponent attempts — elite rim protection."})

    spg = _f("diff_spg")
    raw.append({"name": "Steals per Game", "value": round(spg, 2), "impact": _impact_label(spg),
        "description": f"{_favored(spg)} is the more disruptive defensive team, picking pockets all night "
                       f"({_f('a_espn_stats_spg'):.1f} vs {_f('b_espn_stats_spg'):.1f} SPG)."})

    stl_pct = _f("diff_stl_pct")
    raw.append({"name": "Steal Rate", "value": round(stl_pct, 3), "impact": _impact_label(stl_pct),
        "description": f"{_favored(stl_pct)} forces more turnovers as a percentage of possessions — pressure defense."})

    fouls = _f("diff_fouls_pg")
    raw.append({"name": "Foul Discipline", "value": round(fouls, 2), "impact": _impact_label(fouls),
        "description": f"{_favored(fouls)} commits fewer fouls per game, keeping the opponent off the line "
                       f"({_f('a_espn_stats_fouls_pg'):.1f} vs {_f('b_espn_stats_fouls_pg'):.1f} fouls/game)."})

    # --- Rebounding ---
    rpg = _f("diff_rpg")
    raw.append({"name": "Total Rebounds", "value": round(rpg, 2), "impact": _impact_label(rpg),
        "description": f"{_favored(rpg)} is winning the battle on the boards "
                       f"({_f('a_espn_stats_rpg'):.1f} vs {_f('b_espn_stats_rpg'):.1f} RPG)."})

    orpg = _f("diff_orpg")
    raw.append({"name": "Offensive Rebounds", "value": round(orpg, 2), "impact": _impact_label(orpg),
        "description": f"{_favored(orpg)} crashes the offensive glass harder, creating more second chances "
                       f"({_f('a_espn_stats_orpg'):.1f} vs {_f('b_espn_stats_orpg'):.1f} ORPG)."})

    orb = _f("diff_orb_pct")
    raw.append({"name": "Off. Rebound Rate", "value": round(orb, 3), "impact": _impact_label(orb),
        "description": f"{_favored(orb)} grabs a higher percentage of available offensive rebounds — relentless pursuit."})

    drb = _f("diff_drb_pct")
    raw.append({"name": "Def. Rebound Rate", "value": round(drb, 3), "impact": _impact_label(drb),
        "description": f"{_favored(drb)} locks down the defensive glass better, denying second-chance opportunities."})

    # --- Playmaking ---
    apg = _f("diff_apg")
    raw.append({"name": "Assists per Game", "value": round(apg, 2), "impact": _impact_label(apg),
        "description": f"{_favored(apg)} moves the ball better and generates more team-based scoring "
                       f"({_f('a_espn_stats_apg'):.1f} vs {_f('b_espn_stats_apg'):.1f} APG)."})

    ast_to = _f("diff_ast_to_ratio")
    raw.append({"name": "Assist/Turnover Ratio", "value": round(ast_to, 3), "impact": _impact_label(ast_to),
        "description": f"{_favored(ast_to)} has the better AST/TO ratio — more ball movement, fewer mistakes."})

    topg = _f("diff_topg")
    raw.append({"name": "Turnovers per Game", "value": round(topg, 2), "impact": _impact_label(topg),
        "description": f"{_favored(topg)} takes better care of the ball, giving up fewer possessions "
                       f"({_f('b_espn_stats_topg'):.1f} vs {_f('a_espn_stats_topg'):.1f} TOPG)."})

    tov_pct = _f("diff_tov_pct")
    raw.append({"name": "Turnover Rate", "value": round(tov_pct, 3), "impact": _impact_label(tov_pct),
        "description": f"{_favored(tov_pct)} turns the ball over on fewer possessions — better decision-making."})

    ast_pct = _f("diff_ast_pct")
    raw.append({"name": "Assist Rate", "value": round(ast_pct, 3), "impact": _impact_label(ast_pct),
        "description": f"{_favored(ast_pct)} assists on a higher percentage of made baskets — true team basketball."})

    # --- Roster / Experience ---
    exp = _f("diff_experience")
    raw.append({"name": "Roster Experience", "value": round(exp, 3), "impact": _impact_label(exp),
        "description": f"{_favored(exp)} has a more experienced roster — more juniors and seniors who've been here before."})

    rot = _f("diff_rotation_size")
    raw.append({"name": "Bench Depth", "value": round(rot, 0), "impact": _impact_label(rot),
        "description": f"{_favored(rot)} has a deeper rotation — more contributors who can absorb foul trouble and fatigue."})

    conc = _f("diff_usage_concentration")
    raw.append({"name": "Team Balance", "value": round(conc, 3), "impact": _impact_label(conc),
        "description": f"{_favored(conc)} spreads usage more evenly — harder to game-plan against, less star-dependent."})

    # --- Coaching ---
    cwp = _f("diff_coach_win_pct")
    raw.append({"name": "Coach Win %", "value": round(cwp, 3), "impact": _impact_label(cwp),
        "description": f"{_favored(cwp)}'s coach has a stronger career winning record "
                       f"({_f('a_coach_win_pct'):.0%} vs {_f('b_coach_win_pct'):.0%})."})

    ctr = _f("diff_coach_tourney_rate")
    raw.append({"name": "Coach Tournament History", "value": round(ctr, 3), "impact": _impact_label(ctr),
        "description": f"{_favored(ctr)}'s coach has more experience in big tournament moments — that matters late."})

    # --- Tournament context ---
    seed_d = _f("diff_seed")
    if abs(seed_d) > 0.5:
        raw.append({"name": "Tournament Seed", "value": round(seed_d, 0), "impact": _impact_label(seed_d),
            "description": f"{_favored(seed_d)} is the higher seed — the selection committee gave them the edge "
                           f"(#{int(_f('a_seed'))} vs #{int(_f('b_seed'))})."})

    # --- Home court ---
    hc = _f("home_court_advantage")
    if hc > 0:
        hc_desc = f"{team_a_name} has home-court advantage — their crowd will be electric tonight."
    elif hc < 0:
        hc_desc = f"{team_b_name} has home-court advantage — {team_a_name} is walking into a hostile arena."
    else:
        hc_desc = "Neutral site — no home-court edge for either team. This is a pure basketball matchup."
    raw.append({"name": "Home Court", "value": hc, "impact": _impact_label(hc), "description": hc_desc})

    # --- Player momentum ---
    hp = _f("diff_hot_players")
    raw.append({"name": "Hot Players", "value": round(hp, 0), "impact": _impact_label(hp),
        "description": f"{_favored(hp)} has more players playing above their season average right now "
                       f"({int(_f('a_hot_players_count'))} vs {int(_f('b_hot_players_count'))})."})

    conf_wp = _f("diff_conf_win_pct")
    raw.append({"name": "Conference Win %", "value": round(conf_wp, 3), "impact": _impact_label(conf_wp),
        "description": f"{_favored(conf_wp)} performed better within their conference this season — tougher competition."})

    # Sort: non-neutral by absolute magnitude first, neutral at the end
    non_neutral = [f for f in raw if f["impact"] != "neutral"]
    neutral = [f for f in raw if f["impact"] == "neutral"]
    non_neutral.sort(key=lambda f: abs(f["value"]), reverse=True)

    return non_neutral + neutral


def build_summary(
    features: dict,
    team_a_name: str,
    team_b_name: str,
    team_a_prob: float,
) -> str:
    """
    Generate a casual, commentator-style summary from real feature values.
    Tone: hype basketball broadcast — punchy, opinionated, natural slang.
    """
    favored = team_a_name if team_a_prob >= 0.5 else team_b_name
    underdog = team_b_name if team_a_prob >= 0.5 else team_a_name
    pct = max(team_a_prob, 1 - team_a_prob) * 100

    # Opening line scales with confidence level
    if pct >= 80:
        opener = (
            f"Look, I'm not gonna sugarcoat it — {favored} should run away with this one. "
            f"We're talking a {pct:.0f}% win probability. {underdog} is gonna need a miracle."
        )
    elif pct >= 65:
        opener = (
            f"Alright, the numbers are pretty clear here — {favored} is the play at {pct:.0f}%. "
            f"That doesn't mean {underdog} can't pull off the upset, but it's an uphill battle."
        )
    elif pct >= 55:
        opener = (
            f"This one's leaning {favored}'s way, but don't sleep on {underdog}. "
            f"{pct:.0f}% says {favored} gets it done — this could go down to the wire."
        )
    else:
        opener = (
            f"Folks, this is a legit coin flip. {favored} edges it at {pct:.0f}% but honestly "
            f"anyone who tells you they know how this ends is lying to you."
        )

    parts: list[str] = [opener]

    # Season record / strength
    pdiff = features.get("diff_point_diff", 0.0)
    if abs(pdiff) > 5:
        better = team_a_name if pdiff > 0 else team_b_name
        val = features.get("a_espn_point_differential", 0.0) if pdiff > 0 else features.get("b_espn_point_differential", 0.0)
        parts.append(f"{better} has been DOMINANT this season — averaging {val:+.1f} points per game. That kind of margin doesn't lie.")

    rnk = features.get("diff_rank", 0.0)
    if abs(rnk) > 5:
        better = team_a_name if rnk > 0 else team_b_name
        parts.append(f"The national rankings back this up — {better} has been one of the best teams in the country all year.")

    # Momentum
    streak = features.get("diff_streak", 0.0)
    if abs(streak) >= 2:
        better = team_a_name if streak > 0 else team_b_name
        parts.append(f"{better} is riding serious momentum right now — you can feel the energy building.")

    # Shooting
    fg = features.get("diff_fg_pct", 0.0)
    if abs(fg) > 0.02:
        better = team_a_name if fg > 0 else team_b_name
        fav_efg = features.get("a_fg_pct", 0.0) if fg > 0 else features.get("b_fg_pct", 0.0)
        parts.append(f"{better} has been absolutely cooking from the field — {fav_efg:.1%} effective shooting is hard to stop.")

    tp = features.get("diff_three_pct", 0.0)
    if abs(tp) > 0.03:
        better = team_a_name if tp > 0 else team_b_name
        parts.append(f"{better} is dialed in from deep right now — their shooters are locked in and that's dangerous.")

    ft = features.get("diff_ft_pct", 0.0)
    if abs(ft) > 0.06:
        better = team_a_name if ft > 0 else team_b_name
        worse = team_b_name if ft > 0 else team_a_name
        parts.append(
            f"You do NOT want to send {better} to the line — they're automatic. "
            f"{worse}, on the other hand, has been a liability at the stripe."
        )

    # Defense
    bpg = features.get("diff_bpg", 0.0)
    if abs(bpg) > 0.8:
        better = team_a_name if bpg > 0 else team_b_name
        parts.append(f"{better} is a wall at the rim — their shot-blocking has been elite, and driving lanes are going to be tough.")

    spg = features.get("diff_spg", 0.0)
    if abs(spg) > 0.5:
        better = team_a_name if spg > 0 else team_b_name
        parts.append(f"{better}'s defense is relentless — they're getting into passing lanes and creating havoc.")

    # Rebounding
    rpg = features.get("diff_rpg", 0.0)
    if abs(rpg) > 2.0:
        better = team_a_name if rpg > 0 else team_b_name
        parts.append(f"{better} is winning the glass battle and that usually translates directly into wins — extra possessions are priceless.")

    # Playmaking
    ast_to = features.get("diff_ast_to_ratio", 0.0)
    if abs(ast_to) > 0.2:
        better = team_a_name if ast_to > 0 else team_b_name
        parts.append(f"{better} is playing real team basketball — better ball movement, smarter decisions, the whole package.")

    topg = features.get("diff_topg", 0.0)
    if abs(topg) > 1.5:
        better = team_a_name if topg > 0 else team_b_name
        parts.append(f"{better} takes way better care of the ball — turnovers kill you in March and they know it.")

    # Experience
    exp = features.get("diff_experience", 0.0)
    if abs(exp) > 0.4:
        better = team_a_name if exp > 0 else team_b_name
        parts.append(f"Experience matters in March Madness, and {better} has the veterans who've been in big games before.")

    # Coaching
    cwp = features.get("diff_coach_win_pct", 0.0)
    if abs(cwp) > 0.05:
        better = team_a_name if cwp > 0 else team_b_name
        parts.append(f"Coaching matters in big moments, and {better}'s bench has the résumé to back it up.")

    # Hot players
    hp = features.get("diff_hot_players", 0.0)
    if abs(hp) >= 2:
        better = team_a_name if hp > 0 else team_b_name
        parts.append(f"{better} has got multiple guys in a groove right now — when that happens, it's a nightmare to defend.")

    # Seed context
    seed_d = features.get("diff_seed", 0.0)
    if abs(seed_d) >= 3:
        better = team_a_name if seed_d > 0 else team_b_name
        worse = team_b_name if seed_d > 0 else team_a_name
        parts.append(f"The committee gave {better} the edge on Selection Sunday — {worse} is going to have to prove everyone wrong.")

    # Home court
    hc = features.get("home_court_advantage", 0.0)
    if hc != 0:
        home = team_a_name if hc > 0 else team_b_name
        away = team_b_name if hc > 0 else team_a_name
        parts.append(
            f"And let's not forget — {home} is at home. That crowd is going to be absolutely electric. "
            f"{away} has gotta block all that noise out."
        )

    return " ".join(parts)
