"""Per-parlay background refresh tasks.

One asyncio task per parlay while its game has not yet finished. Runs every
60 seconds; each iteration offloads the blocking nba_api call onto a thread
so the event loop stays responsive.
"""
import asyncio
import logging
from datetime import date
from typing import Dict

from database import SessionLocal
from models import Parlay
import crud

POLL_INTERVAL_SECONDS = 60

log = logging.getLogger(__name__)

# parlay_id -> asyncio.Task
_active_tasks: Dict[int, asyncio.Task] = {}

# The main event loop, captured at app startup. Sync route handlers run in a
# threadpool so they can't use asyncio.get_event_loop() directly.
_main_loop: asyncio.AbstractEventLoop | None = None


def set_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _main_loop
    _main_loop = loop


async def _run_parlay_loop(parlay_id: int) -> None:
    """Refresh loop for a single parlay. Exits when parlay is no longer pending
    or when game_date is in the past."""
    while True:
        try:
            await asyncio.to_thread(_refresh_once, parlay_id)
        except Exception as e:
            log.exception("refresh failed for parlay %s: %s", parlay_id, e)

        # Decide whether to keep polling
        should_continue = await asyncio.to_thread(_should_continue, parlay_id)
        if not should_continue:
            log.info("parlay %s loop exiting", parlay_id)
            _active_tasks.pop(parlay_id, None)
            return

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


def _refresh_once(parlay_id: int) -> None:
    db = SessionLocal()
    try:
        parlay = db.query(Parlay).filter(Parlay.id == parlay_id).first()
        if parlay is None:
            return
        crud.refresh_parlay(db, parlay)
    finally:
        db.close()


def _should_continue(parlay_id: int) -> bool:
    db = SessionLocal()
    try:
        parlay = db.query(Parlay).filter(Parlay.id == parlay_id).first()
        if parlay is None:
            return False
        # Stop if game_date is in the past (we'll give it one final check cycle
        # on the day itself before stopping)
        try:
            game_date = date.fromisoformat(parlay.game_date)
        except ValueError:
            return False
        if game_date < date.today():
            return False
        # Stop once parlay status is resolved
        if parlay.status in ("hit", "miss"):
            return False
        return True
    finally:
        db.close()


def start_parlay_task(parlay_id: int) -> None:
    """Idempotent: starts a background task for this parlay if not already running.
    Safe to call from sync handlers running in a threadpool."""
    if parlay_id in _active_tasks and not _active_tasks[parlay_id].done():
        return
    if _main_loop is None:
        log.warning("main loop not set; skipping task for parlay %s", parlay_id)
        return

    def _schedule() -> None:
        task = _main_loop.create_task(_run_parlay_loop(parlay_id))
        _active_tasks[parlay_id] = task

    _main_loop.call_soon_threadsafe(_schedule)


def cancel_parlay_task(parlay_id: int) -> None:
    task = _active_tasks.pop(parlay_id, None)
    if task and not task.done():
        task.cancel()


async def start_all_pending() -> None:
    """On app startup, start a task for every pending parlay whose game_date is today or future."""
    db = SessionLocal()
    try:
        today = date.today()
        pending = (
            db.query(Parlay).filter(Parlay.status == "pending").all()
        )
        for p in pending:
            try:
                gd = date.fromisoformat(p.game_date)
            except ValueError:
                continue
            if gd >= today:
                start_parlay_task(p.id)
    finally:
        db.close()
