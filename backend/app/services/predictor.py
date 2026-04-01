from __future__ import annotations

import logging
import math

import numpy as np

from app.core.config import FALLBACK_WEIGHTS, MODEL_PATH

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model loading (cached at module level)
# ---------------------------------------------------------------------------

_model = None
_model_loaded = False


def load_model():
    """Attempt to load the trained sklearn model once."""
    global _model, _model_loaded
    if _model_loaded:
        return _model

    _model_loaded = True

    if not MODEL_PATH.exists():
        logger.info("No trained model found at %s — using fallback.", MODEL_PATH)
        return None

    try:
        import joblib
        _model = joblib.load(MODEL_PATH)
        logger.info("Loaded trained model from %s", MODEL_PATH)
    except Exception as exc:
        logger.error("Failed to load model: %s — using fallback.", exc)
        _model = None

    return _model


# ---------------------------------------------------------------------------
# Feature vector for the trained model (must match training column order)
# ---------------------------------------------------------------------------

FEATURE_COLUMNS = [
    # Season strength (ESPN)
    "diff_win_pct",
    "diff_conf_win_pct",
    "diff_ppg",
    "diff_oppg",
    "diff_point_diff",
    "diff_rank",
    # Momentum
    "diff_streak",
    "diff_win_rate_5",
    "diff_win_rate_10",
    "diff_avg_margin_5",
    "diff_avg_margin_10",
    "diff_win_streak",
    "diff_hot_players",
    # Shooting (Barttorvik / ESPN)
    "diff_fg_pct",
    "diff_efg_pct",
    "diff_ts_pct",
    "diff_two_pct",
    "diff_three_pct",
    "diff_ft_pct",
    "diff_three_rate",
    "diff_ft_rate",
    "diff_clutch_fg_pct",
    "diff_scoring_eff",
    # Defense
    "diff_bpg",
    "diff_spg",
    "diff_blk_pct",
    "diff_stl_pct",
    "diff_fouls_pg",
    # Rebounding
    "diff_rpg",
    "diff_orpg",
    "diff_drpg",
    "diff_orb_pct",
    "diff_drb_pct",
    # Playmaking
    "diff_apg",
    "diff_topg",
    "diff_ast_to_ratio",
    "diff_tov_pct",
    "diff_ast_pct",
    # Roster
    "diff_experience",
    "diff_rotation_size",
    "diff_usage_concentration",
    # Coaching
    "diff_coach_win_pct",
    "diff_coach_tourney_rate",
    # Tournament
    "diff_seed",
    # Venue
    "home_court_advantage",
]


def _features_to_array(features: dict) -> np.ndarray:
    """Convert feature dict to a 1-row numpy array in the model's expected order."""
    row = [float(features.get(col, 0.0)) for col in FEATURE_COLUMNS]
    return np.array([row])


# ---------------------------------------------------------------------------
# Fallback deterministic predictor
# ---------------------------------------------------------------------------

def _sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    ex = math.exp(x)
    return ex / (1.0 + ex)


def _clamp(val: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, val))


def _fallback_predict(features: dict) -> float:
    """
    Multi-category weighted heuristic.
    Each category contributes a normalised signal in [-1, 1].
    Final score is passed through a scaled sigmoid → clipped probability.
    """
    w = FALLBACK_WEIGHTS

    def _g(key: str, scale: float, lo: float = -1.0, hi: float = 1.0) -> float:
        return _clamp(features.get(key, 0.0) / scale, lo, hi)

    # --- Season strength ---
    win_pct    = _g("diff_win_pct",    0.30)
    conf_wp    = _g("diff_conf_win_pct", 0.25)
    ppg        = _g("diff_ppg",        15.0)
    oppg       = _g("diff_oppg",       15.0)
    pt_diff    = _g("diff_point_diff", 15.0)
    rank       = _g("diff_rank",       20.0)

    # --- Shooting ---
    efg        = _g("diff_efg_pct",    0.10)
    three      = _g("diff_three_pct",  0.10)
    ft         = _g("diff_ft_pct",     0.10)
    two        = _g("diff_two_pct",    0.10)
    ts         = _g("diff_ts_pct",     0.10)

    # --- Defense ---
    blk_pg     = _g("diff_bpg",        2.0)
    stl_pg     = _g("diff_spg",        2.0)
    blk_r      = _g("diff_blk_pct",    3.0)
    stl_r      = _g("diff_stl_pct",    1.5)

    # --- Rebounding ---
    rpg        = _g("diff_rpg",        6.0)
    orpg       = _g("diff_orpg",       3.0)
    orb        = _g("diff_orb_pct",    8.0)
    drb        = _g("diff_drb_pct",    8.0)

    # --- Playmaking ---
    apg        = _g("diff_apg",        4.0)
    topg       = _g("diff_topg",       4.0)
    ast_to     = _g("diff_ast_to_ratio", 0.6)
    tov_pct    = _g("diff_tov_pct",    8.0)

    # --- Momentum ---
    streak     = _g("diff_streak",     5.0)
    wr5        = _g("diff_win_rate_5", 0.50)
    hot        = _g("diff_hot_players", 3.0)

    # --- Experience / depth ---
    exp        = _g("diff_experience", 1.5)
    rotation   = _g("diff_rotation_size", 4.0)

    # --- Tournament / venue ---
    seed       = _g("diff_seed",       8.0)
    home       = features.get("home_court_advantage", 0.0)

    raw = (
        w["win_pct_diff"]         * win_pct
        + w["conf_win_pct_diff"]  * conf_wp
        + w["ppg_diff"]           * ppg
        + w["oppg_diff"]          * oppg
        + w["rank_diff"]          * rank
        + w["efg_pct_diff"]       * efg
        + w["three_pct_diff"]     * three
        + w["ft_pct_diff"]        * ft
        + w["two_pct_diff"]       * two
        + w["ts_pct_diff"]        * ts
        + w["blk_pg_diff"]        * blk_pg
        + w["stl_pg_diff"]        * stl_pg
        + w["blk_pct_diff"]       * blk_r
        + w["stl_pct_diff"]       * stl_r
        + w["rpg_diff"]           * rpg
        + w["orb_pct_diff"]       * orb
        + w["drb_pct_diff"]       * drb
        + w["apg_diff"]           * apg
        + w["topg_diff"]          * topg
        + w["ast_to_ratio_diff"]  * ast_to
        + w["tov_pct_diff"]       * tov_pct
        + w["streak_diff"]        * streak
        + w["scoring_eff_diff"]   * _g("diff_scoring_eff", 0.3)
        + w["hot_players_diff"]   * hot
        + w["experience_diff"]    * exp
        + w["rotation_diff"]      * rotation
        + w["seed_diff"]          * seed
        + w["home_court"]         * home * 0.3
        + w["fouls_pg_diff"]      * _g("diff_fouls_pg", 4.0)
        + w["ft_rate_diff"]       * _g("diff_ft_rate", 0.20)
    )

    prob = _sigmoid(raw * 4.0)
    return max(0.05, min(0.95, prob))


# ---------------------------------------------------------------------------
# Public predict function
# ---------------------------------------------------------------------------

def predict_from_features(features: dict) -> dict:
    """
    Return prediction dict with:
      - team_a_win_probability
      - team_b_win_probability
      - confidence
      - model_used
    """
    model = load_model()

    if model is not None:
        try:
            X = _features_to_array(features)
            proba = model.predict_proba(X)[0]
            if hasattr(model, "classes_"):
                class_list = list(model.classes_)
                idx = class_list.index(1) if 1 in class_list else 1
            else:
                idx = 1
            team_a_prob = float(proba[idx])
            team_a_prob = max(0.05, min(0.95, team_a_prob))
            model_used = "trained_model"
        except Exception as exc:
            logger.error("Model prediction failed: %s — falling back.", exc)
            team_a_prob = _fallback_predict(features)
            model_used = "fallback"
    else:
        team_a_prob = _fallback_predict(features)
        model_used = "fallback"

    team_b_prob = 1.0 - team_a_prob
    confidence = abs(team_a_prob - 0.5) * 2.0  # 0 = coin flip, 1 = certain

    return {
        "team_a_win_probability": round(team_a_prob, 4),
        "team_b_win_probability": round(team_b_prob, 4),
        "confidence": round(confidence, 4),
        "model_used": model_used,
    }
