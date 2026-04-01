"""
Fetches per-team season stats and records from the ESPN public API.

No API key required. Two endpoints used:
  /teams/{id}             → win%, records, PPG, OPPG, differential, streak, rank
  /teams/{id}/statistics  → FG%, 3PT%, FT%, 2PT%, RPG, ORPG, DRPG, APG, TOPG,
                            BPG, SPG, fouls/game, AST/TO ratio, scoring efficiency

Both responses are cached for 1 hour in-process.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import requests

from app.core.config import ESPN_TEAMS_BASE_URL

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 8
_CACHE: dict[str, Any] = {}
_CACHE_TTL = 3600  # 1 hour


def _cache_get(key: str) -> Any | None:
    entry = _CACHE.get(key)
    if entry and (time.time() - entry["ts"]) < _CACHE_TTL:
        return entry["data"]
    return None


def _cache_set(key: str, data: Any) -> None:
    _CACHE[key] = {"data": data, "ts": time.time()}


def _safe(val: Any, default: float = 0.0) -> float:
    try:
        v = float(val)
        return v if v == v else default
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------

def _fetch_team_profile(espn_id: str) -> dict:
    """Fetch /teams/{id} and return the raw 'team' dict."""
    key = f"profile_{espn_id}"
    cached = _cache_get(key)
    if cached is not None:
        return cached

    try:
        resp = requests.get(
            f"{ESPN_TEAMS_BASE_URL}/{espn_id}",
            timeout=_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json().get("team", {})
        _cache_set(key, data)
        return data
    except Exception as exc:
        logger.warning("ESPN team profile failed for id %s: %s", espn_id, exc)
        return {}


def _fetch_team_statistics(espn_id: str) -> dict:
    """Fetch /teams/{id}/statistics and return flat {stat_name: value} dict."""
    key = f"stats_{espn_id}"
    cached = _cache_get(key)
    if cached is not None:
        return cached

    try:
        resp = requests.get(
            f"{ESPN_TEAMS_BASE_URL}/{espn_id}/statistics",
            timeout=_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        raw = resp.json()
        flat: dict[str, float] = {}
        categories = raw.get("results", {}).get("stats", {}).get("categories", [])
        for cat in categories:
            for stat in cat.get("stats", []):
                name = stat.get("name", "")
                val = stat.get("value")
                if name and val is not None:
                    flat[name] = _safe(val)
        _cache_set(key, flat)
        return flat
    except Exception as exc:
        logger.warning("ESPN team statistics failed for id %s: %s", espn_id, exc)
        return {}


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def get_team_record(espn_id: str) -> dict:
    """
    Return season record and high-level performance metrics for a team.

    Keys returned:
      win_pct, conf_win_pct, home_win_pct, away_win_pct,
      ppg, oppg, point_differential,
      streak (positive = win streak, negative = loss streak),
      rank (AP/curated rank, lower is better; 99 if unranked)
    """
    profile = _fetch_team_profile(espn_id)
    if not profile:
        return _default_record()

    record_items = profile.get("record", {}).get("items", [])
    record_map: dict[str, dict] = {}
    for item in record_items:
        rtype = item.get("type", "")
        stats_list = item.get("stats", [])
        record_map[rtype] = {s["name"]: _safe(s.get("value", 0)) for s in stats_list}

    overall = record_map.get("total", {})
    home = record_map.get("home", {})
    away = record_map.get("road", {})

    win_pct = _safe(overall.get("winPercent", 0.5))
    ppg = _safe(overall.get("avgPointsFor", 70.0))
    oppg = _safe(overall.get("avgPointsAgainst", 70.0))
    differential = _safe(overall.get("differential", 0.0))
    streak_val = _safe(overall.get("streak", 0.0))

    home_win_pct = _safe(home.get("winPercent", 0.5))
    away_win_pct = _safe(away.get("winPercent", 0.5))

    # Conference win% from leagueWinPercent field
    conf_win_pct = _safe(overall.get("leagueWinPercent", win_pct))

    # Curated rank (AP/coaches poll proxy); ESPN stores it in nextEvent or rank field
    rank = _safe(profile.get("rank", 99))
    if rank == 0:
        rank = 99.0  # unranked

    return {
        "win_pct": round(win_pct, 4),
        "conf_win_pct": round(conf_win_pct, 4),
        "home_win_pct": round(home_win_pct, 4),
        "away_win_pct": round(away_win_pct, 4),
        "ppg": round(ppg, 2),
        "oppg": round(oppg, 2),
        "point_differential": round(differential, 2),
        "streak": round(streak_val, 1),
        "rank": rank,
    }


def get_team_stats(espn_id: str) -> dict:
    """
    Return per-game shooting and box-score stats from ESPN season statistics.

    Keys returned:
      fg_pct, three_pct, ft_pct, two_pt_pct,
      rpg, orpg, drpg,
      apg, topg, ast_to_ratio,
      bpg, spg, fouls_pg,
      scoring_efficiency, shooting_efficiency
    """
    s = _fetch_team_statistics(espn_id)
    if not s:
        return _default_stats()

    # FG%: ESPN stores as 0-100, convert to 0-1
    fg_pct = _safe(s.get("fieldGoalPct", 45.0)) / 100.0
    three_pct = _safe(s.get("threePointFieldGoalPct", 33.0)) / 100.0
    ft_pct = _safe(s.get("freeThrowPct", 70.0)) / 100.0
    two_pct = _safe(s.get("twoPointFieldGoalPct", 50.0)) / 100.0

    # Rebounds
    rpg = _safe(s.get("avgRebounds", 35.0))
    orpg = _safe(s.get("avgOffensiveRebounds", 10.0))
    drpg = rpg - orpg  # ESPN doesn't always have avgDefensiveRebounds directly

    # Playmaking
    apg = _safe(s.get("avgAssists", 13.0))
    topg = _safe(s.get("avgTurnovers", 12.0))
    ast_to = _safe(s.get("assistTurnoverRatio", apg / max(topg, 1)))

    # Defense
    bpg = _safe(s.get("avgBlocks", 3.5))
    spg = _safe(s.get("avgSteals", 6.5))
    fouls_pg = _safe(s.get("avgFouls", 17.0))

    # Efficiency
    scoring_eff = _safe(s.get("scoringEfficiency", 1.2))
    shooting_eff = _safe(s.get("shootingEfficiency", 0.5))

    # Derived: FT rate (FTA / FGA)
    fta_pg = _safe(s.get("avgFreeThrowsAttempted", 18.0))
    fga_pg = _safe(s.get("avgFieldGoalsAttempted", 62.0))
    ft_rate = fta_pg / max(fga_pg, 1.0)

    # 3-point attempt rate
    three_pa_pg = _safe(s.get("avgThreePointFieldGoalsAttempted", 24.0))
    three_rate = three_pa_pg / max(fga_pg, 1.0)

    return {
        "fg_pct": round(fg_pct, 4),
        "three_pct": round(three_pct, 4),
        "ft_pct": round(ft_pct, 4),
        "two_pt_pct": round(two_pct, 4),
        "rpg": round(rpg, 2),
        "orpg": round(orpg, 2),
        "drpg": round(drpg, 2),
        "apg": round(apg, 2),
        "topg": round(topg, 2),
        "ast_to_ratio": round(ast_to, 3),
        "bpg": round(bpg, 2),
        "spg": round(spg, 2),
        "fouls_pg": round(fouls_pg, 2),
        "ft_rate": round(ft_rate, 4),
        "three_rate": round(three_rate, 4),
        "scoring_efficiency": round(scoring_eff, 4),
        "shooting_efficiency": round(shooting_eff, 4),
    }


def _default_record() -> dict:
    return {
        "win_pct": 0.5, "conf_win_pct": 0.5,
        "home_win_pct": 0.5, "away_win_pct": 0.5,
        "ppg": 70.0, "oppg": 70.0, "point_differential": 0.0,
        "streak": 0.0, "rank": 99.0,
    }


def _default_stats() -> dict:
    return {
        "fg_pct": 0.45, "three_pct": 0.33, "ft_pct": 0.70, "two_pt_pct": 0.50,
        "rpg": 35.0, "orpg": 10.0, "drpg": 25.0,
        "apg": 13.0, "topg": 12.0, "ast_to_ratio": 1.1,
        "bpg": 3.5, "spg": 6.5, "fouls_pg": 17.0,
        "ft_rate": 0.29, "three_rate": 0.38,
        "scoring_efficiency": 1.2, "shooting_efficiency": 0.50,
    }
