"""Small presentation helpers shared by Home Helper pages."""

from datetime import date, datetime


def parse_datetime(value):
    """Return a datetime for a stored ISO value, or None if it is invalid."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def friendly_date(value, include_time=False):
    """Format ISO dates for people instead of exposing database timestamps."""
    parsed = parse_datetime(value)
    if not parsed:
        return "Date not set"
    date_text = f"{parsed.strftime('%a')} {parsed.day} {parsed.strftime('%b')}"
    if include_time:
        time_text = parsed.strftime("%I:%M %p").lstrip("0")
        return f"{date_text} · {time_text}"
    return date_text


def due_label(value):
    """Return a short, useful due-date label."""
    parsed = parse_datetime(value)
    if not parsed:
        return "No due date"

    due = parsed.date()
    delta = (due - date.today()).days
    if delta < 0:
        return f"Overdue · {friendly_date(value)}"
    if delta == 0:
        return "Due today"
    if delta == 1:
        return "Due tomorrow"
    return f"Due {friendly_date(value)}"
