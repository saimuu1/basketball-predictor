import { useEffect, useRef } from 'react';
import { X, Trophy, Cpu, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import type { PastGame, PredictResponse, UpcomingGame } from '../types';
import { confidenceLabel, formatDate } from '../utils/format';
import ProbabilityBar from './ProbabilityBar';
import FactorsList from './FactorsList';
import LoadingState from './LoadingState';
import ErrorState from './ErrorState';

interface PredictionModalProps {
  game: UpcomingGame | PastGame | null;
  prediction: PredictResponse | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
  onRetry: () => void;
}

export default function PredictionModal({
  game,
  prediction,
  loading,
  error,
  onClose,
  onRetry,
}: PredictionModalProps) {
  const [showAllFactors, setShowAllFactors] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const isPastGame = game !== null && 'team_a_score' in game;

  // Reset factor expansion when game changes
  useEffect(() => {
    setShowAllFactors(false);
  }, [game?.game_id]);

  // Close on Escape key
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  // Prevent background scroll when modal open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  if (!game) return null;

  const visibleFactors = prediction
    ? showAllFactors
      ? prediction.factors
      : prediction.factors.slice(0, 5)
    : [];

  const { label: confLabel, color: confColor } = prediction
    ? confidenceLabel(prediction.confidence)
    : { label: '', color: '' };

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 z-50 flex items-stretch justify-end"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      {/* Dim overlay */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />

      {/* Slide-in panel */}
      <div
        ref={panelRef}
        className="relative z-10 w-full max-w-lg bg-gray-50 shadow-2xl flex flex-col"
        style={{
          maxHeight: '100dvh',
          animation: 'slideInRight 0.28s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        {/* Modal header */}
        <div className="flex items-start justify-between px-5 pt-5 pb-4 bg-white border-b border-gray-100 flex-shrink-0">
          <div className="min-w-0 pr-3">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-0.5">
              {isPastGame ? 'Completed Game · AI Prediction' : 'Upcoming Game · AI Prediction'}
            </p>
            <h2 className="text-base font-bold text-gray-900 leading-tight">
              {game.team_a_name}
              <span className="font-normal text-gray-400 mx-1.5">vs.</span>
              {game.team_b_name}
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">{formatDate(game.game_date)}</p>
          </div>
          <button
            onClick={onClose}
            className="flex-shrink-0 w-8 h-8 rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition-colors"
          >
            <X size={16} className="text-gray-600" />
          </button>
        </div>

        {/* Actual score banner for past games */}
        {isPastGame && (
          <div className="bg-slate-800 px-5 py-3 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-3">
              <div className="text-center">
                <p className="text-xs text-slate-400 font-medium truncate max-w-[110px]">
                  {game.team_a_name}
                </p>
                <p className={`text-3xl font-black ${
                  (game as PastGame).team_a_score > (game as PastGame).team_b_score
                    ? 'text-white'
                    : 'text-slate-500'
                }`}>
                  {(game as PastGame).team_a_score}
                </p>
              </div>
              <div className="text-slate-500 font-bold text-lg pb-1">–</div>
              <div className="text-center">
                <p className="text-xs text-slate-400 font-medium truncate max-w-[110px]">
                  {game.team_b_name}
                </p>
                <p className={`text-3xl font-black ${
                  (game as PastGame).team_b_score > (game as PastGame).team_a_score
                    ? 'text-white'
                    : 'text-slate-500'
                }`}>
                  {(game as PastGame).team_b_score}
                </p>
              </div>
            </div>
            <span className="text-xs text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2.5 py-1 rounded-full font-semibold">
              {(game as PastGame).status}
            </span>
          </div>
        )}

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto px-5 py-5 space-y-4">
          {loading && <LoadingState message="Generating prediction…" />}
          {error && <ErrorState message={error} onRetry={onRetry} />}

          {prediction && !loading && (
            <>
              {/* Winner Banner */}
              <div className="bg-gradient-to-r from-slate-800 to-slate-900 rounded-xl p-4 text-white relative overflow-hidden">
                <div className="absolute inset-0 opacity-10 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-400 to-transparent" />
                <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-1">
                  {isPastGame ? 'Model would have predicted' : 'Predicted Winner'}
                </p>
                <div className="flex items-center gap-2.5">
                  <Trophy size={20} className="text-yellow-400 flex-shrink-0" />
                  <h3 className="text-xl font-extrabold tracking-tight">{prediction.predicted_winner}</h3>
                </div>
                <div className="mt-2 flex items-center gap-2 flex-wrap">
                  <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full bg-white/10 ${confColor}`}>
                    {confLabel}
                  </span>
                  {prediction.model_used === 'fallback' && (
                    <span className="text-xs text-amber-400 flex items-center gap-1">
                      <AlertCircle size={11} /> Heuristic model
                    </span>
                  )}
                  {prediction.model_used === 'trained_model' && (
                    <span className="text-xs text-emerald-400 flex items-center gap-1">
                      <Cpu size={11} /> ML model
                    </span>
                  )}
                </div>
              </div>

              {/* Win Probabilities */}
              <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
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
              <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                  Analysis
                </p>
                <p className="text-sm text-gray-700 leading-relaxed">{prediction.summary}</p>
              </div>

              {/* Key Factors */}
              {prediction.factors.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                    Key Factors
                  </p>
                  <FactorsList
                    factors={visibleFactors}
                    teamAName={game.team_a_name}
                    teamBName={game.team_b_name}
                  />
                  {prediction.factors.length > 5 && (
                    <button
                      onClick={() => setShowAllFactors((v) => !v)}
                      className="mt-3 w-full flex items-center justify-center gap-1.5 text-xs font-medium text-blue-600 hover:text-blue-700 py-1.5 rounded-lg hover:bg-blue-50 transition-colors"
                    >
                      {showAllFactors ? (
                        <><ChevronUp size={14} /> Show less</>
                      ) : (
                        <><ChevronDown size={14} /> Show {prediction.factors.length - 5} more factors</>
                      )}
                    </button>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
