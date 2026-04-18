import logging
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from nba_api.stats.static import players as nba_players, teams as nba_teams
from nba_api.stats.endpoints import ScoreboardV2, CommonPlayerInfo
from nba_api.live.nba.endpoints import boxscore as live_boxscore

log = logging.getLogger(__name__)

# nba.com can be slow but a *very* long timeout (e.g. 30s) means a single
# unresponsive request can dominate a refresh that fans out across many legs.
# 15s is generous enough for a normal response while letting the user see a
# failure within a reasonable window.
NBA_HTTP_TIMEOUT = 15

# In-memory cache: player_id -> team_id. Player's current team rarely changes,
# so caching avoids a CommonPlayerInfo call on every refresh.
_team_cache: Dict[int, int] = {}

# Short TTL cache for the daily scoreboard so matchup lookups + refresh loops
# don't each hit nba.com. Games for a date don't change composition once set.
_GAMES_CACHE_TTL_SECONDS = 60
_games_cache: Dict[str, Tuple[float, List[Dict]]] = {}

# Short TTL cache for per-game box scores so multiple legs in the same game
# (e.g. two Hornets players in one parlay) share a single nba.com fetch per
# refresh cycle instead of hitting the endpoint once per leg.
_BOXSCORE_CACHE_TTL_SECONDS = 30
_boxscore_cache: Dict[str, Tuple[float, Dict]] = {}

# team_id -> abbreviation (e.g. 1610612744 -> "GSW")
_team_abbrev_cache: Dict[int, str] = {}


# ---------- Player search (Stage 3) ----------
def search_players(query: str, limit: int = 10, active_only: bool = True) -> List[Dict]:
    q = query.strip().lower()
    if not q:
        return []

    all_players = nba_players.get_players()
    if active_only:
        all_players = [p for p in all_players if p.get("is_active")]

    starts, contains = [], []
    for p in all_players:
        name = p["full_name"].lower()
        if name.startswith(q):
            starts.append(p)
        elif q in name:
            contains.append(p)

    starts.sort(key=lambda p: p["full_name"])
    contains.sort(key=lambda p: p["full_name"])

    return [
        {"player_id": p["id"], "full_name": p["full_name"]}
        for p in (starts + contains)[:limit]
    ]


# ---------- Stats (Stage 5) ----------
# Maps our stat_type to the key in the live CDN box score's
# `player.statistics` dict. We use the live endpoint because
# BoxScoreTraditionalV2 stopped publishing data in the 2025-26 season and V3's
# parser crashes on live games.
STAT_COLUMNS = {
    "points": "points",
    "rebounds": "reboundsTotal",
    "assists": "assists",
    "steals": "steals",
    "blocks": "blocks",
    "threes_made": "threePointersMade",
}

# ScoreboardV2 game_status_id: 1=scheduled, 2=live, 3=final
STATUS_MAP = {1: "scheduled", 2: "live", 3: "final"}


def _format_scoreboard_date(game_date: str) -> str:
    """Convert YYYY-MM-DD to MM/DD/YYYY for ScoreboardV2."""
    d = datetime.strptime(game_date, "%Y-%m-%d")
    return d.strftime("%m/%d/%Y")


def get_games_on_date(game_date: str) -> List[Dict]:
    """Return all NBA games for a YYYY-MM-DD date.

    Each dict: {game_id, home_team_id, visitor_team_id, status}.
    status is one of: scheduled / live / final / unknown.

    Results are cached in-process for `_GAMES_CACHE_TTL_SECONDS` so that a
    single refresh cycle (and matchup lookups) don't each hit nba.com.
    """
    cached = _games_cache.get(game_date)
    if cached is not None:
        stored_at, games = cached
        if time.time() - stored_at < _GAMES_CACHE_TTL_SECONDS:
            return games

    try:
        sb = ScoreboardV2(
            game_date=_format_scoreboard_date(game_date),
            timeout=NBA_HTTP_TIMEOUT,
        )
    except Exception as e:
        log.warning("ScoreboardV2 failed for %s: %s", game_date, e)
        # Negative-cache so we don't re-hit nba.com for every leg on this date.
        _games_cache[game_date] = (time.time(), [])
        return []
    # GameHeader resultSet columns: GAME_ID, HOME_TEAM_ID, VISITOR_TEAM_ID, GAME_STATUS_ID, ...
    rows = sb.game_header.get_dict()["data"]
    headers = sb.game_header.get_dict()["headers"]
    idx = {h: i for i, h in enumerate(headers)}

    status_text_idx = idx.get("GAME_STATUS_TEXT")

    games = []
    for r in rows:
        status_text = None
        if status_text_idx is not None:
            raw = r[status_text_idx]
            if isinstance(raw, str) and raw.strip():
                status_text = raw.strip()
        games.append(
            {
                "game_id": r[idx["GAME_ID"]],
                "home_team_id": r[idx["HOME_TEAM_ID"]],
                "visitor_team_id": r[idx["VISITOR_TEAM_ID"]],
                "status": STATUS_MAP.get(r[idx["GAME_STATUS_ID"]], "unknown"),
                "status_text": status_text,
            }
        )
    _games_cache[game_date] = (time.time(), games)
    return games


def get_team_abbrev(team_id: int) -> Optional[str]:
    """Return the 3-letter team abbreviation (e.g. "GSW") for a given team_id."""
    if team_id in _team_abbrev_cache:
        return _team_abbrev_cache[team_id]
    try:
        team = nba_teams.find_team_name_by_id(int(team_id))
    except Exception:
        return None
    if not team:
        return None
    abbrev = team.get("abbreviation")
    if abbrev:
        _team_abbrev_cache[team_id] = abbrev
    return abbrev


def get_matchup_for_player(player_id: int, game_date: str) -> Optional[str]:
    """Return a short matchup string from the player's perspective, e.g.
    "vs LAL · 7:30 pm ET" when home pre-game, "@ LAL · Q2 5:23" during the
    game, "@ LAL · Final" after. Returns None if the player's team isn't
    playing on that date or the lookup fails."""
    try:
        team_id = get_player_team_id(player_id)
        if team_id is None:
            return None
        for game in get_games_on_date(game_date):
            home_id, away_id = game["home_team_id"], game["visitor_team_id"]
            if team_id == home_id:
                opp = get_team_abbrev(away_id)
                base = f"vs {opp}" if opp else None
            elif team_id == away_id:
                opp = get_team_abbrev(home_id)
                base = f"@ {opp}" if opp else None
            else:
                continue
            if not base:
                return None
            status_text = game.get("status_text")
            return f"{base} \u00b7 {status_text}" if status_text else base
    except Exception:
        return None
    return None


def get_player_team_id(player_id: int) -> Optional[int]:
    """Return the player's current NBA team_id, or None if unavailable.
    Cached in-process after first lookup."""
    if player_id in _team_cache:
        return _team_cache[player_id]

    try:
        info = CommonPlayerInfo(player_id=player_id, timeout=NBA_HTTP_TIMEOUT)
        data = info.common_player_info.get_dict()
        headers = data["headers"]
        rows = data["data"]
        if not rows:
            return None
        team_idx = headers.index("TEAM_ID")
        team_id = rows[0][team_idx]
        if team_id:
            _team_cache[player_id] = int(team_id)
            return int(team_id)
    except Exception as e:
        log.warning("CommonPlayerInfo failed for player %s: %s", player_id, e)
        return None
    return None


def find_player_game(player_id: int, game_date: str) -> Optional[Dict]:
    """Return the game dict the player's team is playing on game_date, or None.

    Strategy: look up the player's team_id (cached), then match against the
    home/visitor team_ids on the scoreboard — no per-game box-score scans.
    """
    team_id = get_player_team_id(player_id)
    if team_id is None:
        return None

    for game in get_games_on_date(game_date):
        if game["home_team_id"] == team_id or game["visitor_team_id"] == team_id:
            return game
    return None


def _get_boxscore(game_id: str) -> Optional[Dict[int, Dict]]:
    """Fetch the live-CDN box score for a game and return a {player_id: stats}
    dict, with short in-process caching so multiple legs in the same game share
    a single fetch per refresh cycle. Returns None on failure.

    Uses nba_api.live — this endpoint works for both live and final games and
    is the replacement for the deprecated BoxScoreTraditionalV2 (which stopped
    publishing data in the 2025-26 season)."""
    game_id = str(game_id)
    cached = _boxscore_cache.get(game_id)
    if cached is not None:
        stored_at, data = cached
        if time.time() - stored_at < _BOXSCORE_CACHE_TTL_SECONDS:
            return data

    try:
        bs = live_boxscore.BoxScore(game_id=game_id, timeout=NBA_HTTP_TIMEOUT)
        payload = bs.get_dict()
    except Exception as e:
        log.warning("live BoxScore failed for game %s: %s", game_id, e)
        return None

    game = payload.get("game") or {}
    players_by_id: Dict[int, Dict] = {}
    for side in ("homeTeam", "awayTeam"):
        for p in (game.get(side) or {}).get("players", []) or []:
            pid = p.get("personId")
            stats = p.get("statistics")
            if pid is None or stats is None:
                continue
            try:
                players_by_id[int(pid)] = stats
            except (TypeError, ValueError):
                continue

    if not players_by_id:
        log.warning("live BoxScore returned no players for game %s", game_id)

    _boxscore_cache[game_id] = (time.time(), players_by_id)
    return players_by_id


def get_player_stat(player_id: int, game_id: str, stat_type: str) -> Optional[float]:
    """Return the player's value for the given stat in the given game, or None
    if the player didn't play, the stat is missing, or the NBA API is
    unreachable."""
    key = STAT_COLUMNS.get(stat_type)
    if key is None:
        return None

    players = _get_boxscore(game_id)
    if players is None:
        return None

    stats = players.get(int(player_id))
    if stats is None:
        return None

    value = stats.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_leg_update(
    player_id: int, stat_type: str, game_date: str
) -> Tuple[Optional[float], str]:
    """Combined helper for the refresh path.

    Returns (actual_value, game_status) where game_status is one of
    scheduled / live / final / none_found.
    """
    game = find_player_game(player_id, game_date)
    if game is None:
        return None, "none_found"

    if game["status"] == "scheduled":
        return None, "scheduled"

    value = get_player_stat(player_id, game["game_id"], stat_type)
    return value, game["status"]
