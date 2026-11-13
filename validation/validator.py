"""Data integrity, business-rule and anomaly validation."""
import sqlite3
from datetime import datetime
from pathlib import Path
import json

def validate(db_path: str, report_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    checks = []

    def add(name, passed, actual, expected="0 violations", details=""):
        checks.append({"check": name, "passed": bool(passed), "actual": actual,
                       "expected": expected, "details": details})

    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    add("foreign_key_integrity", len(fk) == 0, len(fk))

    for table, key in [("customers","customer_id"),("consents","consent_id"),("sessions","session_id"),
                       ("carts","cart_id"),("cart_lines","cart_line_id"),("campaigns","campaign_id"),
                       ("message_templates","template_id"),("send_attempts","send_id"),("orders","order_id"),
                       ("attributions","attribution_id"),("message_events","event_id")]:
        dup = conn.execute(f"SELECT COUNT(*) FROM (SELECT {key} FROM {table} GROUP BY {key} HAVING COUNT(*)>1)").fetchone()[0]
        add(f"primary_key_unique_{table}", dup == 0, dup)

    bad_dates = conn.execute("""
        SELECT COUNT(*) FROM carts WHERE last_activity_at < created_at
    """).fetchone()[0]
    add("cart_date_ordering", bad_dates == 0, bad_dates)

    stale = conn.execute("""
        SELECT COUNT(*) FROM carts c
        LEFT JOIN (
          SELECT cart_id, SUM(line_total) AS computed_total
          FROM cart_lines GROUP BY cart_id
        ) totals ON totals.cart_id=c.cart_id
        WHERE ABS(c.cart_total - COALESCE(totals.computed_total,0)) > 0.01
    """).fetchone()[0]
    add("cart_total_reconciliation", stale == 0, stale, "0 in clean baseline; injected anomaly expected after injection")

    purchase_after_abandon = conn.execute("""
        SELECT COUNT(*) FROM carts c JOIN orders o ON o.cart_id=c.cart_id
        WHERE o.order_status IN ('PLACED','PAID')
          AND c.abandoned_at IS NOT NULL AND c.abandoned_at > o.order_date
    """).fetchone()[0]
    add("abandonment_after_purchase", purchase_after_abandon == 0, purchase_after_abandon)

    dup_attr = conn.execute("""
        SELECT COUNT(*) FROM (
          SELECT order_id FROM attributions GROUP BY order_id HAVING COUNT(*)>1
        )
    """).fetchone()[0]
    add("duplicate_order_attribution", dup_attr == 0, dup_attr)

    # Independently verify the configured rolling cap (2 sends per channel in 7 days).
    sent_rows = conn.execute("""SELECT customer_id,channel,sent_at FROM send_attempts
        WHERE sent_at IS NOT NULL ORDER BY customer_id,channel,sent_at""").fetchall()
    cap_violations = 0
    from datetime import timedelta
    windows = {}
    for row in sent_rows:
        key = (row["customer_id"], row["channel"])
        current = datetime.fromisoformat(row["sent_at"])
        recent = [t for t in windows.get(key, []) if current - t <= timedelta(days=7)]
        if len(recent) >= 2:
            cap_violations += 1
        recent.append(current)
        windows[key] = recent
    add("frequency_cap_compliance", cap_violations == 0, cap_violations)

    after_optout = conn.execute("""
        SELECT COUNT(*) FROM send_attempts s
        WHERE s.sent_at IS NOT NULL AND EXISTS (
          SELECT 1 FROM consents c WHERE c.customer_id=s.customer_id AND c.channel=s.channel
          AND c.status='WITHDRAWN' AND c.effective_from<=s.sent_at
          AND (c.effective_to IS NULL OR c.effective_to>s.sent_at)
        )
    """).fetchone()[0]
    add("message_after_optout", after_optout == 0, after_optout)

    counts = {}
    for table in ["customers","consents","sessions","carts","cart_lines","campaigns","message_templates",
                  "send_attempts","message_events","orders","attributions","cart_update_events"]:
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()

    result = {"summary": {"checks": len(checks), "passed": sum(c["passed"] for c in checks),
                          "failed": sum(not c["passed"] for c in checks)},
              "row_counts": counts, "checks": checks}
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
