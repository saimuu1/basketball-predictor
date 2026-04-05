"""
Fetches live college basketball schedules from the ESPN public scoreboard API.

No API key required. Scans from today forward up to ESPN_LOOKAHEAD_DAYS days
so that off-day gaps (e.g. between tournament rounds) are bridged automatically.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta

import requests

from app.core.config import ESPN_LOOKAHEAD_DAYS, ESPN_SCOREBOARD_URL

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 8  # seconds
_PAST_LOOKBACK_DAYS = 14


def _fetch_day(game_date: date) -> list[dict]:
    """Return a list of raw ESPN event dicts for a single calendar day."""
    date_str = game_date.strftime("%Y%m%d")
    try:
        resp = requests.get(
            ESPN_SCOREBOARD_URL,
            params={"dates": date_str, "limit": 100},
            timeout=_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("events", [])
    except Exception as exc:
        logger.warning("ESPN fetch failed for %s: %s", date_str, exc)
        return []


def _logo_url(team: dict) -> str | None:
    """Extract the first available team logo URL from an ESPN team dict."""
    logos = team.get("logos", [])
    if logos:
        return logos[0].get("href") or logos[0].get("url")
    # Some endpoints use a nested logo field
    logo = team.get("logo")
    if isinstance(logo, str) and logo:
        return logo
    return None


def _parse_events(events: list[dict]) -> list[dict]:
    """Convert raw ESPN event dicts to our UpcomingGame-compatible dicts.

    Skips any event that ESPN marks as completed so finished games never
    bleed into the upcoming list.
    """
    games: list[dict] = []
    for event in events:
        try:
            status_type = event.get("status", {}).get("type", {})
            if status_type.get("completed", False):
                continue
            description = status_type.get("description", "")
            if "final" in description.lower():
                continue

            competition = event.get("competitions", [{}])[0]
            competitors = competition.get("competitors", [])
            if len(competitors) < 2:
                continue

            home_team: dict | None = None
            away_team: dict | None = None
            for comp in competitors:
                if comp.get("homeAway") == "home":
                    home_team = comp
                else:
                    away_team = comp

            if home_team is None:
                home_team = competitors[0]
            if away_team is None:
                away_team = competitors[1]

            team_a = away_team.get("team", {})
            team_b = home_team.get("team", {})

            venue = competition.get("venue", {})
            neutral = competition.get("neutralSite", False)
            home_team_id = str(team_b.get("id", "")) if not neutral else None

            games.append({
                "game_id": str(event.get("id", "")),
                "game_date": event.get("date", ""),
                "team_a_id": str(team_a.get("id", "")),
                "team_b_id": str(team_b.get("id", "")),
                "team_a_name": team_a.get("displayName", team_a.get("name", "TBD")),
                "team_b_name": team_b.get("displayName", team_b.get("name", "TBD")),
                "team_a_logo": _logo_url(team_a),
                "team_b_logo": _logo_url(team_b),
                "home_team_id": home_team_id,
                "venue": venue.get("fullName", ""),
                "status": description,
            })
        except Exception as exc:
            logger.debug("Could not parse ESPN event %s: %s", event.get("id"), exc)

    return games


def fetch_upcoming_games(
    start: date | None = None,
    lookahead: int = ESPN_LOOKAHEAD_DAYS,
) -> list[dict]:
    """
    Return upcoming games starting from today (or *start*).

    Scans forward day-by-day until the first day with games is found, then
    also includes the immediately following day (handles multi-day windows like
    Final Four weekends). Always uses the real current date, so the app
    automatically shows whatever games ESPN has scheduled at the time of the
    request — whether that is today, next week, or next month.
    """
    if start is None:
        start = date.today()

    all_games: list[dict] = []
    first_hit_date: date | None = None

    for delta in range(lookahead):
        check_date = start + timedelta(days=delta)
        events = _fetch_day(check_date)
        parsed = _parse_events(events)

        if parsed:
            if first_hit_date is None:
                first_hit_date = check_date
            all_games.extend(parsed)
            if first_hit_date is not None and (check_date - first_hit_date).days >= 1:
                break

    logger.info("ESPN client: found %d upcoming game(s)", len(all_games))
    return all_games


def fetch_past_games(
    lookback: int = _PAST_LOOKBACK_DAYS,
) -> list[dict]:
    """
    Return completed (Final) games from the last *lookback* days.

    Scans backwards from yesterday, collects all days that had Final games,
    and returns them sorted newest-first. Includes final scores and team logos.
    """
    today = date.today()
    all_games: list[dict] = []

    for delta in range(0, lookback + 1):
        check_date = today - timedelta(days=delta)
        for event in _fetch_day(check_date):
            game = _parse_completed_event(event)
            if game:
                all_games.append(game)

    logger.info("ESPN client: found %d past game(s) over last %d days", len(all_games), lookback)
    return all_games


def _parse_completed_event(event: dict) -> dict | None:
    """
    Parse a single ESPN event dict into a completed-game dict.
    Returns None if the event is not yet completed.
    """
    try:
        status_type = event.get("status", {}).get("type", {})
        completed = status_type.get("completed", False)
        description = status_type.get("description", "")
        if not completed and "final" not in description.lower():
            return None

        competition = event.get("competitions", [{}])[0]
        competitors = competition.get("competitors", [])
        if len(competitors) < 2:
            return None

        home_team: dict | None = None
        away_team: dict | None = None
        for comp in competitors:
            if comp.get("homeAway") == "home":
                home_team = comp
            else:
                away_team = comp

        if home_team is None:
            home_team = competitors[0]
        if away_team is None:
            away_team = competitors[1]

        team_a = away_team.get("team", {})
        team_b = home_team.get("team", {})

        team_a_score = int(float(away_team.get("score", 0) or 0))
        team_b_score = int(float(home_team.get("score", 0) or 0))

        neutral = competition.get("neutralSite", False)
        home_team_id = str(team_b.get("id", "")) if not neutral else None
        venue = competition.get("venue", {})

        return {
            "game_id": str(event.get("id", "")),
            "game_date": event.get("date", ""),
            "team_a_id": str(team_a.get("id", "")),
            "team_b_id": str(team_b.get("id", "")),
            "team_a_name": team_a.get("displayName", team_a.get("name", "TBD")),
            "team_b_name": team_b.get("displayName", team_b.get("name", "TBD")),
            "team_a_logo": _logo_url(team_a),
            "team_b_logo": _logo_url(team_b),
            "home_team_id": home_team_id,
            "venue": venue.get("fullName", ""),
            "status": description or "Final",
            "team_a_score": team_a_score,
            "team_b_score": team_b_score,
        }
    except Exception as exc:
        logger.debug("Could not parse completed event %s: %s", event.get("id"), exc)
        return None


def fetch_season_games(season_end_year: int) -> list[dict]:
    """
    Fetch ALL completed games for a full college basketball season.

    A season spans from Nov 1 of (season_end_year - 1) through Apr 30 of
    season_end_year — or up to today, whichever is earlier.

    Makes one HTTP call per day (~150 total) so it is only invoked once per
    season; results are persisted to SQLite for instant re-use afterwards.
    """
    start = date(season_end_year - 1, 11, 1)
    end = min(date(season_end_year, 4, 30), date.today() - timedelta(days=1))

    if start > end:
        logger.warning("fetch_season_games: start %s > end %s, returning empty", start, end)
        return []

    total_days = (end - start).days + 1
    all_games: list[dict] = []
    fetched_days = 0

    logger.info(
        "Season backfill: fetching %d days (%s to %s) for season %d",
        total_days, start, end, season_end_year,
    )

    current = start
    while current <= end:
        events = _fetch_day(current)
        for event in events:
            game = _parse_completed_event(event)
            if game:
                all_games.append(game)
        fetched_days += 1
        if fetched_days % 30 == 0:
            logger.info(
                "Season backfill progress: %d/%d days, %d games so far",
                fetched_days, total_days, len(all_games),
            )
        current += timedelta(days=1)

    logger.info(
        "Season backfill complete: %d completed games found for season %d",
        len(all_games), season_end_year,
    )
    return all_games
