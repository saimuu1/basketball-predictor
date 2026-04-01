import { Trophy, Cpu, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import type { PastGame, PredictResponse, UpcomingGame } from '../types';
import { confidenceLabel } from '../utils/format';
import ProbabilityBar from './ProbabilityBar';
import FactorsList from './FactorsList';
import LoadingState from './LoadingState';
import ErrorState from './ErrorState';
import { useState } from 'react';

interface PredictionPanelProps {
  game: UpcomingGame | PastGame | null;
  prediction: PredictResponse | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

export default function PredictionPanel({
  game,
  prediction,
  loading,
  error,
  onRetry,
}: PredictionPanelProps) {
  const [showAllFactors, setShowAllFactors] = useState(false);

  if (!game) return null;

  if (loading) return <LoadingState message="Generating prediction…" />;
  if (error) return <ErrorState message={error} onRetry={onRetry} />;
  if (!prediction) return null;

  const { label: confLabel, color: confColor } = confidenceLabel(prediction.confidence);
  const visibleFactors = showAllFactors
    ? prediction.factors
    : prediction.factors.slice(0, 4);

  return (
    <div className="space-y-5">
      {/* Winner Banner */}
      <div className="bg-gradient-to-r from-slate-800 to-slate-900 rounded-xl p-5 text-white relative overflow-hidden">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-400 to-transparent" />
        <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-1">
          Predicted Winner
        </p>
        <div className="flex items-center gap-3">
          <Trophy size={22} className="text-yellow-400 flex-shrink-0" />
          <h2 className="text-2xl font-extrabold tracking-tight">{prediction.predicted_winner}</h2>
        </div>
        <div className="mt-2 flex items-center gap-2">
          <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full bg-white/10 ${confColor}`}>
            {confLabel}
          </span>
          {prediction.model_used === 'fallback' && (
            <span className="text-xs text-amber-400 flex items-center gap-1">
              <AlertCircle size={11} />
              Heuristic model
            </span>
          )}
          {prediction.model_used === 'trained_model' && (
            <span className="text-xs text-emerald-400 flex items-center gap-1">
              <Cpu size={11} />
              ML model
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

      {/* Summary */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
          Analysis
        </p>
        <p className="text-sm text-gray-700 leading-relaxed">{prediction.summary}</p>
      </div>

      {/* Key Factors */}
      {prediction.factors && prediction.factors.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Key Factors
          </p>
          <FactorsList
            factors={visibleFactors}
            teamAName={game.team_a_name}
            teamBName={game.team_b_name}
          />
          {prediction.factors.length > 4 && (
            <button
              onClick={() => setShowAllFactors((v) => !v)}
              className="mt-3 w-full flex items-center justify-center gap-1.5 text-xs font-medium text-blue-600 hover:text-blue-700 py-1.5 rounded-lg hover:bg-blue-50 transition-colors"
            >
              {showAllFactors ? (
                <>
                  <ChevronUp size={14} /> Show less
                </>
              ) : (
                <>
                  <ChevronDown size={14} /> Show {prediction.factors.length - 4} more factors
                </>
              )}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
