import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { RefreshCw, Search, X } from 'lucide-react';
import type { PastGame, UpcomingGame } from '../types';
import { fetchUpcomingGames, fetchPastGames, searchGames } from '../api/client';
import GameCard from '../components/GameCard';
import PastGamesList from '../components/PastGamesList';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import type { PredictionPageState } from './PredictionPage';

export default function Home() {
  const navigate = useNavigate();

  // Upcoming
  const [games, setGames] = useState<UpcomingGame[]>([]);
  const [gamesLoading, setGamesLoading] = useState(true);
  const [gamesError, setGamesError] = useState<string | null>(null);

  // Past
  const [pastGames, setPastGames] = useState<PastGame[]>([]);
  const [pastLoading, setPastLoading] = useState(true);
  const [pastError, setPastError] = useState<string | null>(null);

  // Search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<PastGame[] | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // --- Loaders ---

  const loadGames = useCallback(async () => {
    setGamesLoading(true);
    setGamesError(null);
    try {
      setGames(await fetchUpcomingGames());
    } catch (e) {
      setGamesError(e instanceof Error ? e.message : 'Failed to load upcoming games');
    } finally {
      setGamesLoading(false);
    }
  }, []);

  const loadPastGames = useCallback(async () => {
    setPastLoading(true);
    setPastError(null);
    try {
      setPastGames(await fetchPastGames());
    } catch (e) {
      setPastError(e instanceof Error ? e.message : 'Failed to load recent results');
    } finally {
      setPastLoading(false);
    }
  }, []);

  const handleGameClick = useCallback(
    (game: UpcomingGame | PastGame) => {
      const state: PredictionPageState = { game };
      navigate(`/predict/${game.game_id}`, { state });
    },
    [navigate]
  );

  // Debounced search — hits the /api/search-games endpoint
  const handleSearchChange = (value: string) => {
    setSearchQuery(value);

    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);

    if (!value.trim()) {
      setSearchResults(null);
      setSearchError(null);
      return;
    }

    searchTimeoutRef.current = setTimeout(async () => {
      setSearchLoading(true);
      setSearchError(null);
      try {
        const results = await searchGames(value.trim(), 2026);
        setSearchResults(results);
      } catch (e) {
        setSearchError(e instanceof Error ? e.message : 'Search failed');
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 400);
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults(null);
    setSearchError(null);
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
  };

  useEffect(() => {
    loadGames();
    loadPastGames();
  }, [loadGames, loadPastGames]);

  // Determine which games to show in the results section
  const isSearchActive = searchQuery.trim().length > 0;
  const q = searchQuery.trim().toLowerCase();
  const matchingUpcoming = isSearchActive
    ? games.filter(
        (g) =>
          g.team_a_name.toLowerCase().includes(q) ||
          g.team_b_name.toLowerCase().includes(q)
      )
    : [];
  const displayedPastGames = isSearchActive && searchResults !== null
    ? searchResults
    : pastGames.slice(0, 6);
  const displayedPastLoading = isSearchActive ? searchLoading : pastLoading;
  const displayedPastError = isSearchActive ? searchError : pastError;
  const displayedPastRetry = isSearchActive ? () => handleSearchChange(searchQuery) : loadPastGames;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">

      {/* ── SEARCH BAR (Prominent, full-width at top) ──────────────────── */}
      <div className="relative">
        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
          {searchLoading ? (
            <svg className="animate-spin w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          ) : (
            <Search size={20} className="text-gray-400" />
          )}
        </div>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => handleSearchChange(e.target.value)}
          placeholder="Search any team…"
          className="w-full pl-12 pr-12 py-4 rounded-2xl border border-gray-200 bg-white shadow-sm text-sm font-medium text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow hover:shadow-md"
        />
        {searchQuery && (
          <button
            onClick={clearSearch}
            className="absolute inset-y-0 right-4 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={18} />
          </button>
        )}
      </div>

      {/* ── UPCOMING GAMES ─────────────────────────────────────────────── */}
      {!isSearchActive && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-gray-900">Upcoming Games</h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Next 7 days · Click any matchup for the AI prediction
              </p>
            </div>
            {!gamesLoading && !gamesError && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400 bg-gray-100 px-2.5 py-1 rounded-full font-medium">
                  {games.length} matchup{games.length !== 1 ? 's' : ''}
                </span>
                <button
                  onClick={loadGames}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                  title="Refresh"
                >
                  <RefreshCw size={14} />
                </button>
              </div>
            )}
          </div>

          {gamesLoading && <LoadingState message="Loading upcoming games…" />}
          {gamesError && <ErrorState message={gamesError} onRetry={loadGames} />}

          {!gamesLoading && !gamesError && games.length === 0 && (
            <div className="flex items-center gap-3 bg-white border border-dashed border-gray-200 rounded-2xl px-5 py-6 shadow-sm">
              <span className="text-2xl">📅</span>
              <div>
                <p className="text-sm font-medium text-gray-600">No upcoming games in the next 7 days</p>
                <p className="text-xs text-gray-400 mt-0.5">Check back closer to the next round.</p>
              </div>
            </div>
          )}

          {!gamesLoading && !gamesError && games.length > 0 && (
            <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-gray-200 scrollbar-track-transparent">
              {games.map((game) => (
                <GameCard
                  key={game.game_id}
                  game={game}
                  isSelected={false}
                  onClick={() => handleGameClick(game)}
                />
              ))}
            </div>
          )}
        </section>
      )}

      {/* ── RECENT RESULTS / SEARCH RESULTS ────────────────────────────── */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-gray-900">
              {isSearchActive
                ? searchResults !== null
                  ? `Results for "${searchQuery}"`
                  : 'Searching…'
                : 'Recent Results'}
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">
              {isSearchActive
                ? searchLoading
                  ? 'Searching…'
                  : (() => {
                      const total = (searchResults?.length ?? 0) + matchingUpcoming.length;
                      return `${total} game${total !== 1 ? 's' : ''} found`;
                    })()
                : 'Last 14 days · Click any result to see what the AI would have predicted'}
            </p>
          </div>
          {!isSearchActive && !pastLoading && !pastError && (
            <button
              onClick={loadPastGames}
              className="flex-shrink-0 p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
              title="Refresh"
            >
              <RefreshCw size={14} />
            </button>
          )}
        </div>

        {/* Matching upcoming games shown inline when searching */}
        {isSearchActive && matchingUpcoming.length > 0 && (
          <div className="mb-6">
            <p className="text-xs font-semibold text-blue-500 uppercase tracking-widest mb-3 px-0.5">
              Upcoming
            </p>
            <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-gray-200 scrollbar-track-transparent">
              {matchingUpcoming.map((game) => (
                <GameCard
                  key={game.game_id}
                  game={game}
                  isSelected={false}
                  onClick={() => handleGameClick(game)}
                />
              ))}
            </div>
          </div>
        )}

        <PastGamesList
          games={displayedPastGames}
          selectedGameId={null}
          onSelect={handleGameClick}
          loading={displayedPastLoading}
          error={displayedPastError}
          onRetry={displayedPastRetry}
        />
      </section>
    </div>
  );
}
