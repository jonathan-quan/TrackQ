# NBA Tracker

A personal NBA parlay tracking dashboard. Add your player prop bets and the app automatically checks real stats to mark each leg as hit or miss.

---

## Tech Stack
| Layer | Technology |
|---|---|
| Frontend | React + Tailwind CSS |
| Backend | FastAPI |
| Database | MySQL via SQLAlchemy (PyMySQL) |
| NBA Data | `nba_api` (free, no key needed) |
| Auth | JWT (python-jose) + bcrypt (passlib) |

---

## Auth
- Sign up with email + username + password
- Log in with email + password
- JWT token stored on frontend to maintain session
- Passwords hashed with bcrypt, never stored as plain text
- No Google OAuth, no email verification

---

## Features
1. Register and log in
2. Create a named parlay with a game date
3. Add legs — search player, pick stat, set line and over/under
4. Stats refresh on-demand and via per-parlay background tasks while games are live
5. Overall parlay hits only if every single leg hits
6. Full history of all past parlays saved in DB

---

## Project Structure
```
parlay-tracker/
├── backend/
│   ├── main.py              # FastAPI app + all routes
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── crud.py              # DB operations
│   ├── auth.py              # JWT + bcrypt helpers
│   ├── database.py          # SQLAlchemy engine + session
│   ├── scheduler.py         # per-parlay live-game polling tasks
│   ├── requirements.txt
│   ├── .env.example         # template for SECRET_KEY
│   ├── .env                 # SECRET_KEY — never commit this
│   ├── services/
│   │   └── nba_service.py   # nba_api calls
│   ├── sql/
│   │   └── init.sql         # one-time DB + user setup
│   └── tests/               # pytest smoke tests
└── frontend/
    └── src/
        ├── pages/
        │   ├── Login.jsx
        │   ├── Register.jsx
        │   ├── Dashboard.jsx      # all parlays overview
        │   └── ParlayDetail.jsx   # legs + live stats
        ├── components/
        │   ├── AddLegModal.jsx    # search player, pick stat, set line
        │   ├── LegCard.jsx        # shows hit / miss / pending
        │   └── ParlayCard.jsx
        ├── api/                   # axios calls to FastAPI
        └── context/               # auth state (JWT)
```

---

## Build Order

### Stage 0 — Project Setup
1. Create `backend/` and `frontend/` folders
2. Initialize git, add `.gitignore` (ignore `.env`, `venv/`, `node_modules/`, `*.db`)
3. Write `requirements.txt` (fastapi, uvicorn, sqlalchemy, pydantic, python-jose, passlib, bcrypt, nba_api, python-dotenv)
4. Create `.env.example` with `SECRET_KEY=` placeholder

### Stage 1 — Backend Foundation
1. Create virtual environment and install `requirements.txt`
2. Run `backend/sql/init.sql` once (`mysql -u root -p < sql/init.sql`) to create the `trackq_db` schema and the dedicated `trackq_user` account
3. `database.py` — MySQL connection and session
4. `models.py` — User, Parlay, ParlayLeg tables
5. `schemas.py` — Pydantic schemas
6. Run the app and confirm tables are created, check `/docs`

### Stage 2 — Auth
1. `auth.py` — bcrypt helpers and JWT logic
2. Register and login routes in `main.py`
3. Test in `/docs` — register a user, login, get back a token

### Stage 3 — NBA Service
1. `nba_service.py` — player search and stat fetching
2. `/search/nba` route in `main.py`
3. Test searching a player name and getting back a real `player_id`

### Stage 4 — Parlay CRUD
1. `crud.py` — all DB operations
2. Parlay and leg routes in `main.py`
3. Test in `/docs` — create a parlay, add a leg using a real `player_id` from Stage 3, delete a parlay

### Stage 5 — Stat Refresh
1. `/parlays/{id}/refresh` — on-demand refresh that pulls stats for all legs in the parlay
2. Per-parlay background task that runs only while the game is live (skip if not started or finished)
3. Update leg `status` and `actual_value` based on line and over/under
4. Test with a live game and watch status flip

### Stage 5.5 — End-to-End Smoke Test
1. From `/docs`: register → login → create parlay → add leg with real player → refresh → confirm status updates
2. Fix any backend bugs here before touching React

### Stage 6 — React Setup
1. Create Vite project and install dependencies (axios, react-router-dom)
2. Set up Tailwind CSS
3. Set up React Router with placeholder pages

### Stage 7 — Auth Pages
1. Set up Axios instance with base URL pointing to `localhost:8000`
2. Set up Auth context to store JWT token
3. Register page — form that calls `/auth/register`
4. Login page — form that calls `/auth/login` and saves token
5. Protected route — redirect to login if no token

### Stage 8 — Dashboard
1. Fetch and display all user parlays
2. Each parlay shows name, date, and overall status badge
3. Click a parlay to go to detail page

### Stage 9 — Parlay Detail
1. Show all legs for a parlay
2. Each leg shows player, stat, line, actual value, hit/miss/pending
3. Call `/parlays/{id}/refresh` on page open, on a 60s interval while mounted, and on manual refresh-button click

### Stage 10 — Add Parlay Flow
1. Button to create a new parlay with a name and date
2. Add leg modal — search player, pick stat, enter line, over/under
3. Save and see it appear on the dashboard

### Stage 11 — Polish
1. Loading states and error messages
2. Green for hit, red for miss, grey for pending
3. Delete parlay button
4. Make it look clean with Tailwind

---

## Database Tables

### Users
- `id` — primary key
- `username` — unique
- `email` — unique
- `password_hash` — bcrypt hashed
- `created_at` — auto

### Parlays
- `id` — primary key
- `user_id` — FK to Users
- `name` — e.g. "Sunday Parlay"
- `game_date` — format YYYY-MM-DD
- `status` — pending / hit / miss
- `created_at` — auto

### ParlayLegs
- `id` — primary key
- `parlay_id` — FK to Parlays
- `player_name` — e.g. "LeBron James"
- `player_id` — from nba_api
- `stat_type` — points / rebounds / assists / steals / blocks / threes_made
- `line` — e.g. 24.5
- `over_under` — over or under
- `actual_value` — filled after game, nullable
- `status` — pending / hit / miss

---

## API Routes

### Auth
| Method | Route | Description |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Login, returns JWT |
| GET | `/auth/me` | Get current user |

### Parlays
| Method | Route | Description |
|---|---|---|
| POST | `/parlays` | Create parlay |
| GET | `/parlays` | Get all user parlays |
| GET | `/parlays/{id}` | Get single parlay + legs |
| DELETE | `/parlays/{id}` | Delete parlay |
| POST | `/parlays/{id}/refresh` | Manually trigger stat refresh |

### Legs
| Method | Route | Description |
|---|---|---|
| POST | `/parlays/{id}/legs` | Add leg to parlay |
| DELETE | `/legs/{id}` | Remove leg |

### Search
| Method | Route | Description |
|---|---|---|
| GET | `/search/nba?name=` | Search NBA players |

---

## Rules

### API
- Always protect routes with `Depends(get_current_user)` except register and login
- Never block a request waiting on nba_api — always use background tasks
- Refresh is on-demand via `/parlays/{id}/refresh`; a per-parlay background task runs only while the game is live
- Only poll legs where `game_date` is today and the game is currently live — skip if not started or finished
- Return `201` on create, `204` on delete, `401` if unauthorized, `404` if not found
- Allow CORS from `http://localhost:5173` and `http://localhost:3000` in development

### Database
- Never write raw SQL — always use SQLAlchemy models and sessions
- A leg hits if `actual_value` beats the line in the correct direction
- A parlay hits only if every leg hits — misses if any single leg misses
- Deleting a parlay cascades and deletes all its legs
- Everything stays pending until nba_api returns a stat for that game date

---

## Running the App

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # add your SECRET_KEY
uvicorn main:app --reload  # runs on http://localhost:8000
                           # swagger docs at /docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev                # runs on http://localhost:5173
```

### Tests
```bash
cd backend
pip install pytest
pytest tests/
```

---

## Phase 2 (Future)
- Google OAuth login
- Parlay win rate and history analytics
