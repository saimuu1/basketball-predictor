import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Trophy, AlertCircle, Cpu, ChevronDown, ChevronUp } from 'lucide-react';
import type { PastGame, PredictResponse, UpcomingGame } from '../types';
import { fetchPrediction } from '../api/client';
import { confidenceLabel, formatDate, shortName } from '../utils/format';
import TeamLogo from '../components/TeamLogo';
import ProbabilityBar from '../components/ProbabilityBar';
import FactorsList from '../components/FactorsList';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';

export interface PredictionPageState {
  game: UpcomingGame | PastGame;
}

export default function PredictionPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as PredictionPageState | null;

  const [prediction, setPrediction] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAllFactors, setShowAllFactors] = useState(false);

  const game = state?.game ?? null;
  const isPastGame = game !== null && 'team_a_score' in game;
  const pastGame = isPastGame ? (game as PastGame) : null;

  const loadPrediction = async (g: UpcomingGame | PastGame) => {
    setLoading(true);
    setError(null);
    setPrediction(null);
    try {
      const data = await fetchPrediction({
        game_id: g.game_id,
        game_date: g.game_date,
        team_a_id: g.team_a_id,
        team_b_id: g.team_b_id,
        team_a_name: g.team_a_name,
        team_b_name: g.team_b_name,
        home_team_id: g.home_team_id,
      });
      setPrediction(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to generate prediction');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!game) {
      navigate('/', { replace: true });
      return;
    }
    loadPrediction(game);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [game?.game_id]);

  if (!game) return null;

  const visibleFactors = prediction
    ? showAllFactors
      ? prediction.factors
      : prediction.factors.slice(0, 6)
    : [];

  const { label: confLabel, color: confColor } = prediction
    ? confidenceLabel(prediction.confidence)
    : { label: '', color: '' };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors group"
          >
            <span className="w-8 h-8 rounded-lg bg-gray-100 group-hover:bg-gray-200 flex items-center justify-center transition-colors">
              <ArrowLeft size={16} />
            </span>
            Back
          </button>
          <div className="h-5 w-px bg-gray-200" />
          <p className="text-sm font-semibold text-gray-700 truncate">
            {shortName(game.team_a_name)}
            <span className="font-normal text-gray-400 mx-1.5">vs.</span>
            {shortName(game.team_b_name)}
          </p>
          <span className="ml-auto text-xs text-gray-400 flex-shrink-0 hidden sm:block">
            {formatDate(game.game_date)}
          </span>
        </div>
      </div>

      {/* Page content */}
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-5">

        {/* Matchup hero card */}
        <div className="bg-slate-900 rounded-2xl p-6 text-white">
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-4">
            {isPastGame ? 'Completed Game · AI Prediction' : 'Upcoming Game · AI Prediction'}
          </p>

          <div className="flex items-center justify-between gap-4">
            {/* Team A */}
            <div className="flex flex-col items-center gap-2 flex-1 text-center">
              <div className="w-16 h-16 rounded-full bg-white/10 flex items-center justify-center">
                <TeamLogo
                  name={game.team_a_name}
                  logoUrl={game.team_a_logo}
                  size={48}
                />
              </div>
              <span className="text-sm font-bold leading-tight">{shortName(game.team_a_name)}</span>
              {pastGame && (
                <span className={`text-4xl font-black tabular-nums ${
                  pastGame.team_a_score > pastGame.team_b_score ? 'text-white' : 'text-slate-500'
                }`}>
                  {pastGame.team_a_score}
                </span>
              )}
            </div>

            {/* Center divider */}
            <div className="flex flex-col items-center gap-1 flex-shrink-0">
              {pastGame ? (
                <>
                  <span className="text-slate-400 text-lg font-bold">–</span>
                  <span className="text-xs text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2.5 py-1 rounded-full font-semibold">
                    {pastGame.status}
                  </span>
                </>
              ) : (
                <span className="text-slate-400 text-sm font-bold">VS</span>
              )}
            </div>

            {/* Team B */}
            <div className="flex flex-col items-center gap-2 flex-1 text-center">
              <div className="w-16 h-16 rounded-full bg-white/10 flex items-center justify-center">
                <TeamLogo
                  name={game.team_b_name}
                  logoUrl={game.team_b_logo}
                  size={48}
                />
              </div>
              <span className="text-sm font-bold leading-tight">{shortName(game.team_b_name)}</span>
              {pastGame && (
                <span className={`text-4xl font-black tabular-nums ${
                  pastGame.team_b_score > pastGame.team_a_score ? 'text-white' : 'text-slate-500'
                }`}>
                  {pastGame.team_b_score}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Loading / Error */}
        {loading && <LoadingState message="Generating prediction…" />}
        {error && (
          <ErrorState
            message={error}
            onRetry={() => game && loadPrediction(game)}
          />
        )}

        {prediction && !loading && (
          <>
            {/* Predicted winner */}
            <div className="bg-gradient-to-r from-slate-800 to-slate-900 rounded-2xl p-5 text-white relative overflow-hidden">
              <div className="absolute inset-0 opacity-10 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-400 to-transparent pointer-events-none" />
              <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-2">
                {isPastGame ? 'Model would have predicted' : 'Predicted Winner'}
              </p>
              <div className="flex items-center gap-3">
                <Trophy size={24} className="text-yellow-400 flex-shrink-0" />
                <h2 className="text-2xl font-extrabold tracking-tight">{prediction.predicted_winner}</h2>
              </div>
              <div className="mt-3 flex items-center gap-2 flex-wrap">
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full bg-white/10 ${confColor}`}>
                  {confLabel}
                </span>
                {prediction.model_used === 'fallback' && (
                  <span className="text-xs text-amber-400 flex items-center gap-1">
                    <AlertCircle size={12} /> Heuristic model
                  </span>
                )}
                {prediction.model_used === 'trained_model' && (
                  <span className="text-xs text-emerald-400 flex items-center gap-1">
                    <Cpu size={12} /> ML model
                  </span>
                )}
              </div>
            </div>

            {/* Win probability */}
            <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
                Win Probability
              </p>
              <ProbabilityBar
                teamAName={game.team_a_name}
                teamBName={game.team_b_name}
                teamAProb={prediction.team_a_win_probability}
                teamBProb={prediction.team_b_win_probability}
              />
            </div>

            {/* Analysis */}
            <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Analysis
              </p>
              <p className="text-sm text-gray-700 leading-relaxed">{prediction.summary}</p>
            </div>

            {/* Key Factors */}
            {prediction.factors.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
                  Key Factors
                </p>
                <FactorsList
                  factors={visibleFactors}
                  teamAName={game.team_a_name}
                  teamBName={game.team_b_name}
                />
                {prediction.factors.length > 6 && (
                  <button
                    onClick={() => setShowAllFactors((v) => !v)}
                    className="mt-4 w-full flex items-center justify-center gap-1.5 text-xs font-medium text-blue-600 hover:text-blue-700 py-2 rounded-xl hover:bg-blue-50 transition-colors"
                  >
                    {showAllFactors ? (
                      <><ChevronUp size={14} /> Show less</>
                    ) : (
                      <><ChevronDown size={14} /> Show {prediction.factors.length - 6} more factors</>
                    )}
                  </button>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
