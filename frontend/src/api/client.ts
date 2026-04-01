import type { PastGame, PredictRequest, PredictResponse, UpcomingGame } from '../types';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error');
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchUpcomingGames(): Promise<UpcomingGame[]> {
  const res = await fetch(`${BASE_URL}/api/upcoming-games`);
  return handleResponse<UpcomingGame[]>(res);
}

export async function fetchPastGames(): Promise<PastGame[]> {
  const res = await fetch(`${BASE_URL}/api/past-games`);
  return handleResponse<PastGame[]>(res);
}

export async function searchGames(team: string, season?: number): Promise<PastGame[]> {
  const params = new URLSearchParams({ team });
  if (season) params.set('season', String(season));
  const res = await fetch(`${BASE_URL}/api/search-games?${params.toString()}`);
  return handleResponse<PastGame[]>(res);
}

export async function fetchPrediction(request: PredictRequest): Promise<PredictResponse> {
  const res = await fetch(`${BASE_URL}/api/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse<PredictResponse>(res);
}
