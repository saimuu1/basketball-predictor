import { BarChart2 } from 'lucide-react';
import type { PastGame } from '../types';
import { formatDate, shortName } from '../utils/format';
import TeamLogo from './TeamLogo';

interface PastGameCardProps {
  game: PastGame;
  isSelected: boolean;
  onClick: () => void;
}

export default function PastGameCard({ game, isSelected, onClick }: PastGameCardProps) {
  const aWon = game.team_a_score > game.team_b_score;
  const bWon = game.team_b_score > game.team_a_score;
  const margin = Math.abs(game.team_a_score - game.team_b_score);

  return (
    <button
      onClick={onClick}
      className={`w-full text-left rounded-xl border transition-all duration-150 group ${
        isSelected
          ? 'bg-blue-50 border-blue-400 ring-2 ring-blue-400 shadow-md'
          : 'bg-white border-gray-200 hover:border-blue-300 hover:shadow-md shadow-sm'
      }`}
    >
      <div className="p-4">
        {/* Header row */}
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-green-600 bg-green-50 border border-green-200 px-2 py-0.5 rounded-full">
            {game.status}
          </span>
          <span className="text-xs text-gray-400">{formatDate(game.game_date)}</span>
        </div>

        {/* Score block */}
        <div className="space-y-2">
          {/* Team A row */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5 min-w-0">
              <TeamLogo name={game.team_a_name} logoUrl={game.team_a_logo} size={28} />
              <span className={`text-sm truncate ${
                aWon ? 'font-bold text-gray-900' : 'font-medium text-gray-400'
              }`}>
                {shortName(game.team_a_name)}
              </span>
            </div>
            <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
              {aWon && (
                <span className="text-xs font-bold text-green-600">W</span>
              )}
              <span className={`text-xl font-black tabular-nums ${
                aWon ? 'text-gray-900' : 'text-gray-400'
              }`}>
                {game.team_a_score}
              </span>
            </div>
          </div>

          {/* Team B row */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5 min-w-0">
              <TeamLogo name={game.team_b_name} logoUrl={game.team_b_logo} size={28} />
              <span className={`text-sm truncate ${
                bWon ? 'font-bold text-gray-900' : 'font-medium text-gray-400'
              }`}>
                {shortName(game.team_b_name)}
              </span>
            </div>
            <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
              {bWon && (
                <span className="text-xs font-bold text-green-600">W</span>
              )}
              <span className={`text-xl font-black tabular-nums ${
                bWon ? 'text-gray-900' : 'text-gray-400'
              }`}>
                {game.team_b_score}
              </span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-3 pt-2.5 border-t border-gray-100 flex items-center justify-between">
          <span className="text-xs text-gray-400">
            Won by {margin} {margin === 1 ? 'pt' : 'pts'}
          </span>
          <span className={`flex items-center gap-1 text-xs font-medium transition-colors ${
            isSelected ? 'text-blue-600' : 'text-gray-400 group-hover:text-blue-500'
          }`}>
            <BarChart2 size={12} />
            See prediction
          </span>
        </div>
      </div>
    </button>
  );
}
