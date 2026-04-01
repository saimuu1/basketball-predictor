from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from app.models.schemas import (
    HealthResponse,
    PastGame,
    PredictRequest,
    PredictResponse,
    PredictionFactor,
    UpcomingGame,
)
from app.services.data_loader import load_coaches_df, load_games_df, load_players_df, load_upcoming_games_df
from app.services.feature_builder import build_matchup_features, build_feature_factors, build_summary
from app.services.predictor import predict_from_features
from app.services import espn_client, torvik_client, espn_team_client
from app.services import database

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])

# In-memory set of seasons whose full backfill has already been triggered
# during this server session (avoids re-running the ~150 API call walk).
_backfilled_seasons: set[int] = set()

# Minimum number of games we expect in a full season before we skip backfill.
# A typical D1 season has 5,000+ games; we use a low threshold so the first
# search always triggers the full fetch.
_SEASON_BACKFILL_THRESHOLD = 100


def _needs_backfill(season: int) -> bool:
    if season in _backfilled_seasons:
        return False
    count = database.get_season_game_count(season)
    return count < _SEASON_BACKFILL_THRESHOLD


def _run_season_backfill(season: int) -> int:
    """Fetch and store all completed games for *season*. Returns games stored."""
    logger.info("Starting full-season backfill for season %d …", season)
    games = espn_client.fetch_season_games(season_end_year=season)
    stored = database.store_games(games)
    _backfilled_seasons.add(season)
    logger.info("Season %d backfill done: %d games stored", season, stored)
    return stored


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _raw_to_past_game(g: dict) -> PastGame:
    return PastGame(
        game_id=g["game_id"],
        game_date=g.get("game_date", ""),
        team_a_id=g.get("team_a_id", ""),
        team_b_id=g.get("team_b_id", ""),
        team_a_name=g.get("team_a_name", "TBD"),
        team_b_name=g.get("team_b_name", "TBD"),
        home_team_id=g.get("home_team_id"),
        team_a_score=int(g.get("team_a_score") or 0),
        team_b_score=int(g.get("team_b_score") or 0),
        status=g.get("status", "Final"),
        team_a_logo=g.get("team_a_logo"),
        team_b_logo=g.get("team_b_logo"),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="healthy", version="0.1.0")


@router.get("/upcoming-games", response_model=list[UpcomingGame])
def upcoming_games() -> list[UpcomingGame]:
    try:
        live_games = espn_client.fetch_upcoming_games()
        if live_games:
            return [
                UpcomingGame(
                    game_id=g["game_id"],
                    game_date=g["game_date"],
                    team_a_id=g["team_a_id"],
                    team_b_id=g["team_b_id"],
                    team_a_name=g["team_a_name"],
                    team_b_name=g["team_b_name"],
                    home_team_id=g.get("home_team_id"),
                    team_a_logo=g.get("team_a_logo"),
                    team_b_logo=g.get("team_b_logo"),
                )
                for g in live_games
            ]
    except Exception as exc:
        logger.warning("ESPN live games failed, falling back to CSV: %s", exc)

    df = load_upcoming_games_df()
    if df.empty:
        return []

    return [
        UpcomingGame(
            game_id=str(row.get("game_id", "")),
            game_date=str(row.get("game_date", "")),
            team_a_id=str(row.get("team_a_id", "")),
            team_b_id=str(row.get("team_b_id", "")),
            team_a_name=str(row.get("team_a_name", "TBD")),
            team_b_name=str(row.get("team_b_name", "TBD")),
            home_team_id=str(row.get("home_team_id", "")) or None,
        )
        for _, row in df.iterrows()
    ]


@router.get("/past-games", response_model=list[PastGame])
def past_games() -> list[PastGame]:
    try:
        raw = espn_client.fetch_past_games()
        if raw:
            # Persist to DB in the background (best-effort)
            try:
                database.store_games(raw)
            except Exception as exc:
                logger.warning("DB store failed: %s", exc)
            return [_raw_to_past_game(g) for g in raw]
    except Exception as exc:
        logger.warning("ESPN past games failed, falling back to DB: %s", exc)

    # Fall back to local DB
    db_rows = database.get_recent_games(days=14)
    return [_raw_to_past_game(r) for r in db_rows]


@router.get("/search-games", response_model=list[PastGame])
def search_games(
    team: str = Query(..., description="Partial team name to search for"),
    season: int | None = Query(default=None, description="Season year, e.g. 2026"),
) -> list[PastGame]:
    """
    Search completed games stored in the local database.

    On the first search for a given season, this will transparently trigger a
    full-season backfill (Nov 1 → today) which takes 15–30 seconds on first
    call, then serves all results from the local SQLite cache forever after.
    """
    if not team.strip():
        raise HTTPException(status_code=400, detail="team query parameter cannot be empty")

    # Run a full-season backfill the first time this season is searched.
    # After that, results are served instantly from SQLite.
    effective_season = season or 2026
    if _needs_backfill(effective_season):
        try:
            _run_season_backfill(effective_season)
        except Exception as exc:
            logger.warning("Full-season backfill failed, falling back to last 14 days: %s", exc)
            raw = espn_client.fetch_past_games(lookback=14)
            if raw:
                database.store_games(raw)
            _backfilled_seasons.add(effective_season)

    db_results = database.search_games(team.strip(), season=effective_season)
    return [_raw_to_past_game(r) for r in db_results]


@router.post("/backfill-season")
def backfill_season(
    background_tasks: BackgroundTasks,
    season: int = Query(default=2026, description="Season end year to backfill, e.g. 2026"),
    force: bool = Query(default=False, description="Re-run even if already backfilled this session"),
) -> dict:
    """
    Manually trigger a full-season data backfill.

    Runs in the background so the response returns immediately.
    Use GET /api/health to check server status, or watch the backend logs.
    """
    if not force and season in _backfilled_seasons:
        count = database.get_season_game_count(season)
        return {
            "status": "already_done",
            "message": f"Season {season} was already backfilled this session ({count} games in DB).",
        }

    def _bg():
        try:
            _run_season_backfill(season)
        except Exception as exc:
            logger.error("Background backfill for season %d failed: %s", season, exc)

    if force:
        _backfilled_seasons.discard(season)

    background_tasks.add_task(_bg)
    return {
        "status": "started",
        "message": f"Backfill for season {season} started in the background. Check logs for progress.",
    }


@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    games_df = load_games_df()
    players_df = load_players_df()
    coaches_df = load_coaches_df()

    if games_df.empty:
        raise HTTPException(
            status_code=503,
            detail="Historical games data not available. Please add games.csv to data/raw/.",
        )

    torvik_a = torvik_client.get_team_stats(request.team_a_name)
    torvik_b = torvik_client.get_team_stats(request.team_b_name)
    if torvik_a:
        logger.info("Barttorvik stats loaded for %s", request.team_a_name)
    if torvik_b:
        logger.info("Barttorvik stats loaded for %s", request.team_b_name)

    espn_record_a = espn_team_client.get_team_record(request.team_a_id)
    espn_record_b = espn_team_client.get_team_record(request.team_b_id)
    espn_stats_a = espn_team_client.get_team_stats(request.team_a_id)
    espn_stats_b = espn_team_client.get_team_stats(request.team_b_id)
    logger.info(
        "ESPN team data: A win_pct=%.3f  B win_pct=%.3f",
        espn_record_a.get("win_pct", 0.0),
        espn_record_b.get("win_pct", 0.0),
    )

    features = build_matchup_features(
        team_a_id=request.team_a_id,
        team_b_id=request.team_b_id,
        home_team_id=request.home_team_id,
        games_df=games_df,
        players_df=players_df,
        coaches_df=coaches_df,
        torvik_stats_a=torvik_a,
        torvik_stats_b=torvik_b,
        espn_record_a=espn_record_a,
        espn_record_b=espn_record_b,
        espn_stats_a=espn_stats_a,
        espn_stats_b=espn_stats_b,
    )

    prediction = predict_from_features(features)

    factors_raw = build_feature_factors(
        features=features,
        team_a_name=request.team_a_name,
        team_b_name=request.team_b_name,
    )
    factors = [PredictionFactor(**f) for f in factors_raw]

    summary = build_summary(
        features=features,
        team_a_name=request.team_a_name,
        team_b_name=request.team_b_name,
        team_a_prob=prediction["team_a_win_probability"],
    )

    predicted_winner = (
        request.team_a_name
        if prediction["team_a_win_probability"] >= 0.5
        else request.team_b_name
    )

    return PredictResponse(
        predicted_winner=predicted_winner,
        team_a_win_probability=round(prediction["team_a_win_probability"], 3),
        team_b_win_probability=round(prediction["team_b_win_probability"], 3),
        confidence=round(prediction["confidence"], 3),
        summary=summary,
        factors=factors,
        model_used=prediction["model_used"],
    )
