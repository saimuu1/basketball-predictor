# Basketball Predictor

A full-stack college basketball game predictor that uses **live ESPN and Barttorvik data** to predict the outcome of any D1 matchup with win probabilities, key factors, and a commentator-style analysis.

## Features

- **Live upcoming games** — pulls real-time D1 schedules from the ESPN API, updated every time the page loads
- **Game predictions** — weighted heuristic model across 80+ factors including shooting %, coach records, pace, efficiency, and more
- **Full-season search** — search any team to see their full 2025–26 season results and upcoming games
- **Persistent storage** — completed games are stored in SQLite so search results load instantly after the first query
- **Commentator-style analysis** — prediction summaries written in casual, play-by-play language

## Tech Stack

**Backend** — FastAPI, SQLite, ESPN API, Barttorvik API

**Frontend** — React, TypeScript, Vite, Tailwind CSS

## How it works

1. The backend fetches live game schedules from ESPN's public API
2. For each team, it pulls advanced stats from Barttorvik (efficiency ratings, shooting splits, pace, etc.) and season records from ESPN
3. Those stats are turned into ~80 matchup features and run through a weighted heuristic model to produce a win probability
4. Completed games are saved to SQLite — the first search for a season triggers a full backfill of all games since November, stored locally for instant retrieval

## Running locally

### Prerequisites

- Python 3.10+
- Node.js 18+

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### 2. Start the backend

```bash
pip install -r requirements.txt
cd backend
uvicorn app.main:app --reload
```

Backend runs at **http://localhost:8000**. You can explore the API at http://localhost:8000/docs.

### 3. Start the frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:5173** — open that in your browser.

No extra configuration needed. The frontend is pre-configured to talk to `http://localhost:8000` out of the box.
