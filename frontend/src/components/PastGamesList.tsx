import type { PastGame, UpcomingGame } from '../types';
import PastGameCard from './PastGameCard';
import LoadingState from './LoadingState';
import ErrorState from './ErrorState';
import { formatDate } from '../utils/format';

interface PastGamesListProps {
  games: PastGame[];
  selectedGameId: string | null;
  onSelect: (game: PastGame | UpcomingGame) => void;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

function groupByDate(games: PastGame[]): [string, PastGame[]][] {
  const map: Record<string, PastGame[]> = {};
  for (const game of games) {
    const key = formatDate(game.game_date);
    if (!map[key]) map[key] = [];
    map[key].push(game);
  }
  return Object.entries(map).sort((a, b) => {
    const da = new Date(a[1][0].game_date).getTime();
    const db = new Date(b[1][0].game_date).getTime();
    return db - da;
  });
}

export default function PastGamesList({
  games,
  selectedGameId,
  onSelect,
  loading,
  error,
  onRetry,
}: PastGamesListProps) {
  if (loading) return <LoadingState message="Loading results..." />;
  if (error) return <ErrorState message={error} onRetry={onRetry} />;

  if (games.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-14 text-center">
        <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-3 text-2xl">
          🏀
        </div>
        <p className="text-sm font-medium text-gray-600 mb-1">No games found</p>
        <p className="text-xs text-gray-400">Try a different search or check back later.</p>
      </div>
    );
  }

  const grouped = groupByDate(games);

  return (
    <div className="space-y-6">
      {grouped.map(([date, dateGames]) => (
        <div key={date}>
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3 px-0.5">
            {date}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {dateGames.map((game) => (
              <PastGameCard
                key={game.game_id}
                game={game}
                isSelected={selectedGameId === game.game_id}
                onClick={() => onSelect(game)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
