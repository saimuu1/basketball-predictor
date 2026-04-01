"""
Fetches and caches Barttorvik advanced player stats for the current season.

Endpoint: https://barttorvik.com/getadvstats.php?year=YYYY
Returns a JSON array of ~5 000 rows (one per player), no auth required.

Column indices (confirmed from data inspection):
  [0]  player name
  [1]  team name (Barttorvik short form, e.g. "UConn", "North Carolina")
  [2]  conference
  [3]  games played
  [4]  min% (percentage of available minutes)
  [5]  offensive rating
  [6]  usage%
  [7]  eFG% (stored as a percentage, e.g. 64.8 → 0.648)
  [8]  TS%  (stored as a percentage)
  [9]  ORB%
  [10] DRB%
  [11] AST%
  [12] TO%
  [13] FTM  (cumulative)
  [14] FTA  (cumulative)
  [15] FT%  (decimal, e.g. 0.75)
  [16] 2PM  (cumulative)
  [17] 2PA
  [18] 2P%  (decimal)
  [19] 3PM  (cumulative)
  [20] 3PA
  [21] 3P%  (decimal)
  [22] BLK% (rate: % of opp 2PA blocked)
  [23] STL% (rate: % of opp possessions stolen)
  [24] pts per 40 min
  [31] season year
"""
from __future__ import annotations

import logging
import time
from datetime import date
from typing import Any

import requests

from app.core.config import TORVIK_ADVSTATS_URL

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 12
_CACHE: dict[str, Any] = {}
_CACHE_TTL = 3600  # 1 hour


# ---------------------------------------------------------------------------
# ESPN display name → Barttorvik short name mapping
# This is needed because ESPN uses "UConn Huskies" while Torvik uses "UConn".
# ---------------------------------------------------------------------------
_ESPN_TO_TORVIK: dict[str, str] = {
    # Full display names
    "UConn Huskies": "UConn",
    "Connecticut Huskies": "UConn",
    "Illinois Fighting Illini": "Illinois",
    "Michigan Wolverines": "Michigan",
    "Arizona Wildcats": "Arizona",
    "Duke Blue Devils": "Duke",
    "North Carolina Tar Heels": "North Carolina",
    "Kansas Jayhawks": "Kansas",
    "Kentucky Wildcats": "Kentucky",
    "Gonzaga Bulldogs": "Gonzaga",
    "Houston Cougars": "Houston",
    "Auburn Tigers": "Auburn",
    "Tennessee Volunteers": "Tennessee",
    "Alabama Crimson Tide": "Alabama",
    "Iowa State Cyclones": "Iowa St.",
    "Iowa Hawkeyes": "Iowa",
    "Wisconsin Badgers": "Wisconsin",
    "Purdue Boilermakers": "Purdue",
    "Michigan State Spartans": "Michigan St.",
    "Ohio State Buckeyes": "Ohio St.",
    "Indiana Hoosiers": "Indiana",
    "Maryland Terrapins": "Maryland",
    "Rutgers Scarlet Knights": "Rutgers",
    "Penn State Nittany Lions": "Penn St.",
    "Northwestern Wildcats": "Northwestern",
    "Nebraska Cornhuskers": "Nebraska",
    "Minnesota Golden Gophers": "Minnesota",
    "UCLA Bruins": "UCLA",
    "USC Trojans": "USC",
    "Oregon Ducks": "Oregon",
    "Oregon State Beavers": "Oregon St.",
    "Washington Huskies": "Washington",
    "Washington State Cougars": "Washington St.",
    "Utah Utes": "Utah",
    "Colorado Buffaloes": "Colorado",
    "California Golden Bears": "California",
    "Stanford Cardinal": "Stanford",
    "Arizona State Sun Devils": "Arizona St.",
    "Florida Gators": "Florida",
    "Florida State Seminoles": "Florida St.",
    "Georgia Bulldogs": "Georgia",
    "LSU Tigers": "LSU",
    "Mississippi State Bulldogs": "Mississippi St.",
    "Ole Miss Rebels": "Ole Miss",
    "South Carolina Gamecocks": "South Carolina",
    "Vanderbilt Commodores": "Vanderbilt",
    "Arkansas Razorbacks": "Arkansas",
    "Missouri Tigers": "Missouri",
    "Texas A&M Aggies": "Texas A&M",
    "Oklahoma Sooners": "Oklahoma",
    "Texas Longhorns": "Texas",
    "Kansas State Wildcats": "Kansas St.",
    "TCU Horned Frogs": "TCU",
    "Baylor Bears": "Baylor",
    "Texas Tech Red Raiders": "Texas Tech",
    "West Virginia Mountaineers": "West Virginia",
    "Cincinnati Bearcats": "Cincinnati",
    "BYU Cougars": "BYU",
    "UCF Knights": "UCF",
    "Oklahoma State Cowboys": "Oklahoma St.",
    "St. John's Red Storm": "St. John's",
    "Georgetown Hoyas": "Georgetown",
    "Providence Friars": "Providence",
    "Villanova Wildcats": "Villanova",
    "Marquette Golden Eagles": "Marquette",
    "Xavier Musketeers": "Xavier",
    "Creighton Bluejays": "Creighton",
    "Seton Hall Pirates": "Seton Hall",
    "Butler Bulldogs": "Butler",
    "DePaul Blue Demons": "DePaul",
    "Wake Forest Demon Deacons": "Wake Forest",
    "Notre Dame Fighting Irish": "Notre Dame",
    "Louisville Cardinals": "Louisville",
    "Pittsburgh Panthers": "Pittsburgh",
    "Virginia Cavaliers": "Virginia",
    "Virginia Tech Hokies": "Virginia Tech",
    "Georgia Tech Yellow Jackets": "Georgia Tech",
    "Syracuse Orange": "Syracuse",
    "Boston College Eagles": "Boston College",
    "Miami Hurricanes": "Miami FL",
    "NC State Wolfpack": "NC State",
    "Clemson Tigers": "Clemson",
    "Saint Mary's Gaels": "Saint Mary's",
    "San Diego State Aztecs": "San Diego St.",
    "Utah State Aggies": "Utah St.",
    "New Mexico Lobos": "New Mexico",
    "Boise State Broncos": "Boise St.",
    "UNLV Rebels": "UNLV",
    "Colorado State Rams": "Colorado St.",
    "Wyoming Cowboys": "Wyoming",
    "Air Force Falcons": "Air Force",
    "Fresno State Bulldogs": "Fresno St.",
    "Nevada Wolf Pack": "Nevada",
    "Memphis Tigers": "Memphis",
    "SMU Mustangs": "SMU",
    "Wichita State Shockers": "Wichita St.",
    "Tulsa Golden Hurricane": "Tulsa",
    "East Carolina Pirates": "East Carolina",
    "Temple Owls": "Temple",
    "South Florida Bulls": "South Florida",
    "Navy Midshipmen": "Navy",
    "Tulane Green Wave": "Tulane",
    "Charlotte 49ers": "Charlotte",
    "UAB Blazers": "UAB",
    "Florida Atlantic Owls": "Florida Atlantic",
    "Florida International Panthers": "Florida Intl",
    "North Texas Mean Green": "North Texas",
    "Rice Owls": "Rice",
    "UTSA Roadrunners": "UT San Antonio",
    "Dayton Flyers": "Dayton",
    "George Mason Patriots": "George Mason",
    "VCU Rams": "VCU",
    "Richmond Spiders": "Richmond",
    "Saint Louis Billikens": "Saint Louis",
    "Davidson Wildcats": "Davidson",
    "George Washington Colonials": "George Washington",
    "Fordham Rams": "Fordham",
    "Duquesne Dukes": "Duquesne",
    "Rhode Island Rams": "Rhode Island",
    "La Salle Explorers": "La Salle",
    "Massachusetts Minutemen": "Massachusetts",
    # Short name aliases (ESPN sometimes uses abbreviated names)
    "UConn": "UConn",
    "Illinois": "Illinois",
    "Michigan": "Michigan",
    "Arizona": "Arizona",
    "Duke": "Duke",
    "North Carolina": "North Carolina",
    "Kansas": "Kansas",
    "Kentucky": "Kentucky",
}


def _normalize_team_name(espn_name: str) -> str:
    """Map an ESPN display name to its Barttorvik equivalent."""
    if espn_name in _ESPN_TO_TORVIK:
        return _ESPN_TO_TORVIK[espn_name]
    # Fallback: try stripping mascot (last word) from full name
    parts = espn_name.split()
    if len(parts) >= 2:
        no_mascot = " ".join(parts[:-1])
        if no_mascot in _ESPN_TO_TORVIK:
            return _ESPN_TO_TORVIK[no_mascot]
    return espn_name


def _fetch_raw(year: int) -> list[list]:
    """Fetch raw Barttorvik player rows, using an in-memory time cache."""
    cache_key = f"torvik_{year}"
    cached = _CACHE.get(cache_key)
    if cached and (time.time() - cached["ts"]) < _CACHE_TTL:
        return cached["data"]

    try:
        resp = requests.get(
            TORVIK_ADVSTATS_URL,
            params={"year": year},
            timeout=_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        _CACHE[cache_key] = {"data": data, "ts": time.time()}
        logger.info("Barttorvik: fetched %d player rows for %d", len(data), year)
        return data
    except Exception as exc:
        logger.warning("Barttorvik fetch failed for year %d: %s", year, exc)
        return []


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        v = float(val)
        return v if v == v else default  # NaN check
    except (TypeError, ValueError):
        return default


_CLASS_YEAR = {"Fr": 1.0, "So": 2.0, "Jr": 3.0, "Sr": 4.0, "Gr": 4.5}


def _compute_team_stats(rows: list[list]) -> dict:
    """
    Aggregate player rows for one team into an exhaustive set of stats.

    Column references (confirmed):
      [3]  games played
      [4]  min% (0-100, pct of available minutes)
      [6]  usage%
      [7]  eFG% (as pct, e.g. 64.8)
      [8]  TS% (as pct)
      [9]  ORB%    [10] DRB%
      [11] AST%    [12] TO%
      [13] FTM     [14] FTA   [15] FT% (decimal)
      [16] 2PM     [17] 2PA   [18] 2P% (decimal)
      [19] 3PM     [20] 3PA   [21] 3P% (decimal)
      [22] BLK%    [23] STL%
      [25] class year string (Fr/So/Jr/Sr/Gr)
    """
    total_fga = total_efg_num = 0.0
    total_2pa = total_2pm = 0.0
    total_3pa = total_3pm = 0.0
    total_fta = total_ftm = 0.0

    weight_sum = 0.0
    blk_w = ast_w = stl_w = orb_w = drb_w = to_w = ts_w = 0.0
    exp_w = 0.0  # experience (class year weighted)
    usage_sq_sum = 0.0  # for Herfindahl concentration index

    contributor_count = 0  # players with meaningful minutes (min% > 10)

    for row in rows:
        games = _safe_float(row[3])
        min_pct = _safe_float(row[4])
        usage = _safe_float(row[6])
        weight = usage * min_pct * max(games, 1)

        # Shooting totals (cumulative)
        two_pm_r = _safe_float(row[16])
        two_pa_r = _safe_float(row[17])
        three_pm_r = _safe_float(row[19])
        three_pa_r = _safe_float(row[20])
        ftm_r = _safe_float(row[13])
        fta_r = _safe_float(row[14])

        fga = two_pa_r + three_pa_r
        fgm = two_pm_r + three_pm_r

        total_2pa += two_pa_r
        total_2pm += two_pm_r
        total_3pa += three_pa_r
        total_3pm += three_pm_r
        total_fta += fta_r
        total_ftm += ftm_r
        total_fga += fga
        # eFG numerator: (FGM + 0.5*3PM) / FGA
        total_efg_num += fgm + 0.5 * three_pm_r

        # TS% is stored as percentage (e.g. 63.5) — weight by FGA+0.44*FTA
        ts_denom = fga + 0.44 * fta_r
        ts_weighted = (_safe_float(row[8]) / 100.0) * ts_denom
        ts_w += ts_weighted
        total_fga += 0.0  # already counted above

        # Rate stats
        blk_w += _safe_float(row[22]) * weight
        ast_w += _safe_float(row[11]) * weight
        stl_w += _safe_float(row[23]) * weight
        orb_w += _safe_float(row[9]) * weight
        drb_w += _safe_float(row[10]) * weight
        to_w += _safe_float(row[12]) * weight
        weight_sum += weight

        # Experience
        class_str = str(row[25]) if len(row) > 25 else "So"
        class_val = _CLASS_YEAR.get(class_str, 2.0)
        exp_w += class_val * min_pct * max(games, 1)

        # Usage concentration (Herfindahl index — higher = more star-dependent)
        usage_sq_sum += (usage / 100.0) ** 2

        # Depth
        if min_pct > 10:
            contributor_count += 1

    # --- Shooting percentages ---
    efg_pct = total_efg_num / total_fga if total_fga > 0 else 0.0
    three_pct = total_3pm / total_3pa if total_3pa > 0 else 0.0
    two_pct = total_2pm / total_2pa if total_2pa > 0 else 0.0
    ft_pct = total_ftm / total_fta if total_fta > 0 else 0.0
    ts_denom_total = total_fga + 0.44 * total_fta
    ts_pct = ts_w / ts_denom_total if ts_denom_total > 0 else 0.0

    # Shot distribution rates
    three_rate = total_3pa / total_fga if total_fga > 0 else 0.0
    ft_rate = total_fta / total_fga if total_fga > 0 else 0.0

    # --- Rate stats ---
    if weight_sum > 0:
        blk_pct = blk_w / weight_sum          # raw BLK% (0-10 range)
        ast_pct = ast_w / weight_sum           # raw AST% (0-40 range)
        stl_pct = stl_w / weight_sum           # raw STL% (0-5 range)
        orb_pct = orb_w / weight_sum           # raw ORB% (0-20 range)
        drb_pct = drb_w / weight_sum           # raw DRB% (0-40 range)
        tov_pct = to_w / weight_sum            # raw TO% (0-30 range)
        # Scale to per-player-per-game approximation for display
        avg_blk = blk_pct / 8.0
        avg_ast = ast_pct / 10.0
        avg_stl = stl_pct / 6.0
        avg_reb = (orb_pct + drb_pct) / 10.0
        avg_to = tov_pct / 8.0
        # Experience (weighted average class year: 1=Fr, 4=Sr)
        exp_weight_total = sum(
            _safe_float(r[4]) * max(_safe_float(r[3]), 1)
            for r in rows
        )
        avg_experience = (exp_w / exp_weight_total) if exp_weight_total > 0 else 2.0
    else:
        blk_pct = ast_pct = stl_pct = orb_pct = drb_pct = tov_pct = 0.0
        avg_blk = avg_ast = avg_stl = avg_reb = avg_to = 0.0
        avg_experience = 2.0

    # Usage concentration: normalize by expected if equal distribution (1/n)
    n = max(len(rows), 1)
    usage_concentration = usage_sq_sum * n  # >1 = concentrated, ~1 = balanced

    return {
        # Shooting
        "fg_pct": round(efg_pct, 4),          # eFG%
        "two_pct": round(two_pct, 4),
        "three_pct": round(three_pct, 4),
        "ft_pct": round(ft_pct, 4),
        "ts_pct": round(ts_pct, 4),
        "clutch_fg_pct": round(efg_pct, 4),   # proxy via eFG%
        "three_rate": round(three_rate, 4),
        "ft_rate": round(ft_rate, 4),
        # Defense / playmaking (scaled to per-player-per-game)
        "avg_blocks": round(avg_blk, 3),
        "avg_assists": round(avg_ast, 3),
        "avg_steals": round(avg_stl, 3),
        "avg_rebounds": round(avg_reb, 3),
        "avg_turnovers": round(avg_to, 3),
        # Rate stats (raw, for diff features)
        "blk_pct": round(blk_pct, 3),
        "stl_pct": round(stl_pct, 3),
        "orb_pct": round(orb_pct, 3),
        "drb_pct": round(drb_pct, 3),
        "ast_pct": round(ast_pct, 3),
        "tov_pct": round(tov_pct, 3),
        # Roster
        "avg_experience": round(avg_experience, 3),
        "rotation_size": float(contributor_count),
        "usage_concentration": round(usage_concentration, 3),
    }


def get_team_stats(espn_team_name: str, year: int | None = None) -> dict | None:
    """
    Return shooting/playmaking stats for a team from Barttorvik.

    Returns None if the team cannot be found or the API is unreachable.
    """
    if year is None:
        year = date.today().year if date.today().month >= 6 else date.today().year

    torvik_name = _normalize_team_name(espn_team_name)
    rows = _fetch_raw(year)
    if not rows:
        return None

    team_rows = [r for r in rows if r[1] == torvik_name]
    if not team_rows:
        # Try case-insensitive match as fallback
        torvik_lower = torvik_name.lower()
        team_rows = [r for r in rows if str(r[1]).lower() == torvik_lower]

    if not team_rows:
        logger.warning("Barttorvik: no rows found for team '%s' (mapped from '%s')", torvik_name, espn_team_name)
        return None

    stats = _compute_team_stats(team_rows)
    logger.debug("Barttorvik stats for %s: %s", torvik_name, stats)
    return stats
