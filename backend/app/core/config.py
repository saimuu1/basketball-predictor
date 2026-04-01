from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Data paths
# ---------------------------------------------------------------------------
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

RAW_GAMES_PATH = RAW_DIR / "games.csv"
RAW_PLAYERS_PATH = RAW_DIR / "players.csv"
RAW_COACHES_PATH = RAW_DIR / "coaches.csv"
RAW_UPCOMING_GAMES_PATH = RAW_DIR / "upcoming_games.csv"

PROCESSED_GAMES_PATH = PROCESSED_DIR / "cleaned_games.csv"
MODEL_DATASET_PATH = PROCESSED_DIR / "model_dataset.csv"

# ---------------------------------------------------------------------------
# Model artifacts
# ---------------------------------------------------------------------------
MODEL_DIR = PROJECT_ROOT / "ml" / "artifacts"
MODEL_PATH = MODEL_DIR / "model.pkl"

# ---------------------------------------------------------------------------
# Feature windows
# ---------------------------------------------------------------------------
RECENT_WINDOW_SHORT = 5
RECENT_WINDOW_LONG = 10

# ---------------------------------------------------------------------------
# Required columns per dataset (used by data_loader for validation)
# ---------------------------------------------------------------------------
REQUIRED_GAMES_COLUMNS = [
    "game_id",
    "game_date",
    "season",
    "team_id",
    "team_name",
    "opponent_id",
    "opponent_name",
    "team_points",
    "opponent_points",
    "team_win",
    "home_away",
]

REQUIRED_PLAYERS_COLUMNS = [
    "player_id",
    "player_name",
    "team_id",
    "game_date",
    "points",
    "rebounds",
    "assists",
    "minutes",
    "fg_made",
    "fg_attempted",
    "three_made",
    "three_attempted",
    "ft_made",
    "ft_attempted",
    "blocks",
    "steals",
    "turnovers",
    "clutch_fg_made",
    "clutch_fg_attempted",
]

REQUIRED_COACHES_COLUMNS = [
    "coach_id",
    "coach_name",
    "team_id",
    "season",
    "wins",
    "losses",
    "tournament_appearances",
    "tournament_wins",
]

REQUIRED_UPCOMING_COLUMNS = [
    "game_id",
    "game_date",
    "team_a_id",
    "team_b_id",
    "team_a_name",
    "team_b_name",
    "home_team_id",
]

# ---------------------------------------------------------------------------
# External API URLs
# ---------------------------------------------------------------------------
ESPN_SCOREBOARD_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball"
    "/mens-college-basketball/scoreboard"
)
ESPN_TEAMS_BASE_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball"
    "/mens-college-basketball/teams"
)
TORVIK_ADVSTATS_URL = "https://barttorvik.com/getadvstats.php"

# How many calendar days ahead to scan if today has no ESPN games
ESPN_LOOKAHEAD_DAYS = 7

# ---------------------------------------------------------------------------
# Fallback predictor weights  (sum = 1.0)
# Category allocations:
#   Team strength  ~25%  |  Shooting ~20%  |  Defense ~12%
#   Rebounding ~8%       |  Playmaking ~8% |  Momentum ~8%
#   Experience ~7%       |  Tournament ~7% |  Fouling ~5%
# ---------------------------------------------------------------------------
FALLBACK_WEIGHTS = {
    # --- Team strength (25%) ---
    "win_pct_diff":         0.09,
    "conf_win_pct_diff":    0.03,
    "ppg_diff":             0.05,
    "oppg_diff":            0.05,
    "rank_diff":            0.03,
    # --- Shooting (20%) ---
    "efg_pct_diff":         0.07,
    "three_pct_diff":       0.04,
    "ft_pct_diff":          0.03,
    "two_pct_diff":         0.03,
    "ts_pct_diff":          0.03,
    # --- Defense (12%) ---
    "blk_pg_diff":          0.04,
    "stl_pg_diff":          0.03,
    "blk_pct_diff":         0.03,
    "stl_pct_diff":         0.02,
    # --- Rebounding (8%) ---
    "rpg_diff":             0.02,
    "orb_pct_diff":         0.03,
    "drb_pct_diff":         0.03,
    # --- Playmaking (8%) ---
    "apg_diff":             0.02,
    "topg_diff":            0.02,
    "ast_to_ratio_diff":    0.02,
    "tov_pct_diff":         0.02,
    # --- Momentum (8%) ---
    "streak_diff":          0.04,
    "scoring_eff_diff":     0.02,
    "hot_players_diff":     0.02,
    # --- Experience / depth (7%) ---
    "experience_diff":      0.04,
    "rotation_diff":        0.03,
    # --- Tournament context (7%) ---
    "seed_diff":            0.05,
    "home_court":           0.02,
    # --- Fouling (5%) ---
    "fouls_pg_diff":        0.02,
    "ft_rate_diff":         0.03,
}
