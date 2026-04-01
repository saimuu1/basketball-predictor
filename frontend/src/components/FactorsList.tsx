import type { Factor } from '../types';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { formatFactorValue } from '../utils/format';

interface FactorsListProps {
  factors: Factor[];
  teamAName: string;
  teamBName: string;
}

export default function FactorsList({ factors, teamAName, teamBName }: FactorsListProps) {
  if (!factors || factors.length === 0) return null;

  const sorted = [...factors].sort((a, b) => Math.abs(b.value) - Math.abs(a.value));

  return (
    <div className="space-y-2">
      {sorted.map((factor, i) => {
        const isA = factor.impact === 'team_a';
        const isB = factor.impact === 'team_b';
        const isNeutral = factor.impact === 'neutral';

        return (
          <div
            key={i}
            className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 border border-gray-100"
          >
            {/* Icon */}
            <div
              className={`flex-shrink-0 mt-0.5 w-7 h-7 rounded-full flex items-center justify-center ${
                isA
                  ? 'bg-blue-100 text-blue-600'
                  : isB
                  ? 'bg-orange-100 text-orange-500'
                  : 'bg-gray-200 text-gray-500'
              }`}
            >
              {isNeutral ? (
                <Minus size={14} />
              ) : isA ? (
                <TrendingUp size={14} />
              ) : (
                <TrendingDown size={14} />
              )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-gray-800 truncate">{factor.name}</p>
                <span
                  className={`text-xs font-semibold whitespace-nowrap px-2 py-0.5 rounded-full ${
                    isA
                      ? 'bg-blue-100 text-blue-700'
                      : isB
                      ? 'bg-orange-100 text-orange-600'
                      : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  {isA
                    ? `Favors ${teamAName}`
                    : isB
                    ? `Favors ${teamBName}`
                    : formatFactorValue(factor.value)}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{factor.description}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
