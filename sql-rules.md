# SQL Rules

## General
- Database: MySQL on `localhost:3306`, schema name `trackq_db`
- Driver: PyMySQL (connection string `mysql+pymysql://...`)
- ORM: SQLAlchemy
- Never write raw SQL, always use SQLAlchemy models and sessions
- All VARCHAR columns must declare a length (e.g. `String(255)`) — MySQL requires it
- Tables use the InnoDB engine (default) so `ON DELETE CASCADE` works

## Tables

### Users
Stores account info for each user.
- `id` — primary key
- `username` — must be unique
- `email` — must be unique
- `password_hash` — bcrypt hashed, never store plain text
- `created_at` — auto set on creation

### Parlays
One parlay belongs to one user and holds multiple legs.
- `id` — primary key
- `user_id` — links to Users table
- `name` — user given name e.g. "Sunday Parlay"
- `game_date` — format YYYY-MM-DD
- `status` — pending, hit, or miss
- `created_at` — auto set on creation

### ParlayLegs
One leg belongs to one parlay. Represents a single player prop bet.
- `id` — primary key
- `parlay_id` — links to Parlays table
- `player_name` — e.g. "LeBron James"
- `player_id` — id from nba_api
- `stat_type` — points, rebounds, assists, steals, blocks, or threes_made
- `line` — the bet line e.g. 24.5
- `over_under` — "over" or "under"
- `actual_value` — filled in after game, nullable until then
- `status` — pending, hit, or miss

## Status Logic
- A leg hits if the actual value beats the line in the correct direction
- A leg misses if it does not
- A parlay hits only if every single leg hits
- A parlay misses if any one leg misses
- Everything stays pending until stats are fetched

## Relationships
- One User has many Parlays
- One Parlay has many ParlayLegs
- Deleting a Parlay also deletes all its legs (cascade delete)