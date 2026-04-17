# API Rules

## General
- All routes prefixed by resource (e.g. `/parlays`, `/auth`, `/legs`)
- All responses in JSON
- Always protect routes with `Depends(get_current_user)` except `/auth/register` and `/auth/login`
- Use background tasks for stats fetching — never block a request waiting on `nba_api`

## Auth Routes
| Method | Route | Description |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Login, returns JWT |
| GET | `/auth/me` | Get current user |

## Parlay Routes
| Method | Route | Description |
|---|---|---|
| POST | `/parlays` | Create parlay |
| GET | `/parlays` | Get all user parlays |
| GET | `/parlays/{id}` | Get single parlay + legs |
| DELETE | `/parlays/{id}` | Delete parlay |
| POST | `/parlays/{id}/refresh` | Fetch real stats + update hit/miss |

## Leg Routes
| Method | Route | Description |
|---|---|---|
| POST | `/parlays/{id}/legs` | Add leg to parlay |
| DELETE | `/legs/{id}` | Remove leg |

## Search Routes
| Method | Route | Description |
|---|---|---|
| GET | `/search/nba?name=` | Search NBA players |

## Live Stat Polling
- Refresh is on-demand via `POST /parlays/{id}/refresh`
- A per-parlay background task runs only while that parlay's game is currently live
- Only poll legs where `game_date` equals today
- Skip legs for games not started or already finished
- This avoids hammering nba.com and getting rate limited

## Status Codes
- `200` success
- `201` created
- `204` deleted (no content)
- `400` bad request (e.g. duplicate email)
- `401` unauthorized
- `404` not found

## CORS
- Allow `http://localhost:5173` and `http://localhost:3000` in development