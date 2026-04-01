import { MapPin, Clock } from 'lucide-react';
import type { UpcomingGame } from '../types';
import { formatDate, shortName } from '../utils/format';
import TeamLogo from './TeamLogo';

interface GameCardProps {
  game: UpcomingGame;
  isSelected: boolean;
  onClick: () => void;
}

export default function GameCard({ game, isSelected, onClick }: GameCardProps) {
  const isHomeA =
    game.home_team_id &&
    game.home_team_id !== 'nan' &&
    game.home_team_id === game.team_a_id;
  const isHomeB =
    game.home_team_id &&
    game.home_team_id !== 'nan' &&
    game.home_team_id === game.team_b_id;
  const isNeutral = !game.home_team_id || game.home_team_id === 'nan';

  return (
    <button
      onClick={onClick}
      className={`flex-shrink-0 w-56 text-left rounded-xl border transition-all duration-150 group ${
        isSelected
          ? 'bg-blue-50 border-blue-400 ring-2 ring-blue-400 shadow-md'
          : 'bg-white border-gray-200 hover:border-blue-300 hover:shadow-md shadow-sm'
      }`}
    >
      <div className="p-3.5">
        {/* Date */}
        <div className="flex items-center gap-1 mb-3">
          <Clock size={11} className="text-gray-400 flex-shrink-0" />
          <p className="text-xs font-medium text-gray-400 truncate">
            {formatDate(game.game_date)}
          </p>
        </div>

        {/* Teams */}
        <div className="space-y-2">
          {/* Team A */}
          <div className="flex items-center gap-2">
            <TeamLogo name={game.team_a_name} logoUrl={game.team_a_logo} size={28} />
            <div className="flex items-center gap-1 min-w-0">
              <span className={`font-semibold text-xs truncate ${isSelected ? 'text-blue-900' : 'text-gray-900'}`}>
                {shortName(game.team_a_name)}
              </span>
              {isHomeA && <MapPin size={10} className="text-gray-400 flex-shrink-0" />}
            </div>
          </div>

          {/* VS divider */}
          <div className="flex items-center gap-2 pl-1">
            <div className="h-px flex-1 bg-gray-100" />
            <span className="text-xs text-gray-300 font-medium">vs</span>
            <div className="h-px flex-1 bg-gray-100" />
          </div>

          {/* Team B */}
          <div className="flex items-center gap-2">
            <TeamLogo name={game.team_b_name} logoUrl={game.team_b_logo} size={28} />
            <div className="flex items-center gap-1 min-w-0">
              <span className={`font-semibold text-xs truncate ${isSelected ? 'text-blue-900' : 'text-gray-900'}`}>
                {shortName(game.team_b_name)}
              </span>
              {isHomeB && <MapPin size={10} className="text-gray-400 flex-shrink-0" />}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-3 pt-2.5 border-t border-gray-100">
          {isNeutral ? (
            <span className="text-xs text-gray-400">Neutral site</span>
          ) : (
            <span className="text-xs text-gray-400">
              {shortName(isHomeA ? game.team_a_name : game.team_b_name)} hosts
            </span>
          )}
        </div>
      </div>
    </button>
  );
}
