"""Always use clock.now() / clock.today() instead of datetime.now(),
so tests can move time (grade lock, add/drop deadline, session timeout)."""
from datetime import datetime

_frozen = None


def now():
    return _frozen or datetime.now()


def today():
    return now().date()


def set_now(value):
    """Tests only: freeze time at `value` (a datetime). set_now(None) unfreezes."""
    global _frozen
    _frozen = value
