import type { UpcomingGame } from '../types';
import GameCard from './GameCard';
import LoadingState from './LoadingState';
import ErrorState from './ErrorState';
import EmptyState from './EmptyState';
import { formatDate } from '../utils/format';

interface UpcomingGamesListProps {
  games: UpcomingGame[];
  selectedGameId: string | null;
  onSelect: (game: UpcomingGame) => void;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

function groupByDate(games: UpcomingGame[]): Record<string, UpcomingGame[]> {
  return games.reduce<Record<string, UpcomingGame[]>>((acc, game) => {
    const key = formatDate(game.game_date);
    if (!acc[key]) acc[key] = [];
    acc[key].push(game);
    return acc;
  }, {});
}

export default function UpcomingGamesList({
  games,
  selectedGameId,
  onSelect,
  loading,
  error,
  onRetry,
}: UpcomingGamesListProps) {
  if (loading) return <LoadingState message="Loading upcoming games..." />;
  if (error) return <ErrorState message={error} onRetry={onRetry} />;
  if (games.length === 0) return <EmptyState />;

  const grouped = groupByDate(games);

  return (
    <div className="space-y-5 pb-6">
      {Object.entries(grouped).map(([date, dateGames]) => (
        <div key={date}>
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2.5 px-0.5">
            {date}
          </h2>
          <div className="space-y-2.5">
            {dateGames.map((game) => (
              <GameCard
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
