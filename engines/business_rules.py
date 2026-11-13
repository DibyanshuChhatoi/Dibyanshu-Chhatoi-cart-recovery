"""Reusable business-rule evaluators for consent, caps and attribution."""
from datetime import datetime, timedelta


def is_abandoned(last_activity_at: str, now: str, inactivity_minutes: int) -> bool:
    last = datetime.fromisoformat(last_activity_at)
    current = datetime.fromisoformat(now)
    return current - last >= timedelta(minutes=inactivity_minutes)


class ConsentRegistry:
    """In-memory effective-dated consent snapshot loaded from persisted consent history."""
    def __init__(self, conn):
        self.records = {}
        rows = conn.execute("""SELECT customer_id,channel,status,effective_from,effective_to
            FROM consents ORDER BY customer_id,channel,effective_from""").fetchall()
        for row in rows:
            self.records.setdefault((row["customer_id"], row["channel"]), []).append(
                (row["status"], datetime.fromisoformat(row["effective_from"]),
                 datetime.fromisoformat(row["effective_to"]) if row["effective_to"] else None)
            )

    def status_at(self, customer_id: str, channel: str, at_time: str) -> str:
        at = datetime.fromisoformat(at_time)
        for status, start, end in reversed(self.records.get((customer_id, channel), [])):
            if start <= at and (end is None or at < end):
                return status
        return "DENIED"  # fail closed when no effective consent exists


class FrequencyCapTracker:
    """Rolling in-memory cap tracker; only successful sends are recorded."""
    def __init__(self):
        self.sent = {}

    def reached(self, customer_id: str, channel: str, at_time: str,
                cap: int, window_days: int) -> bool:
        at = datetime.fromisoformat(at_time)
        cutoff = at - timedelta(days=window_days)
        key = (customer_id, channel)
        recent = [t for t in self.sent.get(key, []) if cutoff <= t <= at]
        self.sent[key] = recent
        return len(recent) >= cap

    def record(self, customer_id: str, channel: str, sent_at: str):
        self.sent.setdefault((customer_id, channel), []).append(datetime.fromisoformat(sent_at))


def consent_at(conn, customer_id: str, channel: str, at_time: str) -> str:
    row = conn.execute("""
        SELECT status FROM consents
        WHERE customer_id=? AND channel=? AND effective_from<=?
          AND (effective_to IS NULL OR effective_to>?)
        ORDER BY effective_from DESC LIMIT 1
    """, (customer_id, channel, at_time, at_time)).fetchone()
    return row["status"] if row else "DENIED"


def frequency_cap_reached(conn, customer_id: str, channel: str, at_time: str,
                           cap: int, window_days: int) -> bool:
    at = datetime.fromisoformat(at_time)
    cutoff = at - timedelta(days=window_days)
    count = conn.execute("""
        SELECT COUNT(*) AS n FROM send_attempts
        WHERE customer_id=? AND channel=? AND sent_at>=? AND sent_at<=?
    """, (customer_id, channel, cutoff.isoformat(), at_time)).fetchone()["n"]
    return count >= cap


def attribution_eligible(click_time: str, order_time: str, window_days: int) -> bool:
    click = datetime.fromisoformat(click_time)
    order = datetime.fromisoformat(order_time)
    delta = order - click
    return timedelta(0) <= delta <= timedelta(days=window_days)
