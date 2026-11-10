"""Background task runner with retries and logging.

Replaces bare `threading.Thread(...).start()` calls, which silently swallow
exceptions and have no retry. `run_background` executes off the request
thread; `_execute_with_retries` is the synchronous, testable core.

This is an interim in-process runner. The same `run_background(fn, ...)`
interface can later be backed by a durable queue (arq/Celery) without changing
call sites — the seam is intentional.
"""
import logging
import threading
import time

logger = logging.getLogger("voiceagent.tasks")


def _execute_with_retries(fn, *, retries=2, delay=0.0, name="task", sleep=time.sleep):
    """Run fn, retrying on exception up to `retries` times. Returns fn's result,
    or None if it never succeeds (the failure is logged, never raised)."""
    attempt = 0
    while True:
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - background work must not crash the worker
            attempt += 1
            logger.warning(
                "background task %s failed (attempt %d/%d): %s",
                name, attempt, retries + 1, exc,
            )
            if attempt > retries:
                logger.error("background task %s gave up after %d attempts", name, attempt)
                return None
            if delay:
                sleep(delay)


def run_background(fn, *, retries=2, delay=0.0, name="task"):
    """Run fn in a daemon thread with retries. Returns the Thread."""
    thread = threading.Thread(
        target=_execute_with_retries,
        args=(fn,),
        kwargs={"retries": retries, "delay": delay, "name": name},
        daemon=True,
    )
    thread.start()
    return thread
