"""Business and data-quality metrics."""
import sqlite3

def calculate(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    carts = conn.execute("SELECT COUNT(*) FROM carts").fetchone()[0]
    abandoned = conn.execute("SELECT COUNT(*) FROM carts WHERE abandoned_at IS NOT NULL").fetchone()[0]
    recovered = conn.execute("SELECT COUNT(*) FROM carts WHERE status='RECOVERED'").fetchone()[0]
    sends = conn.execute("SELECT COUNT(*) FROM send_attempts").fetchone()[0]
    suppressed = conn.execute("SELECT COUNT(*) FROM send_attempts WHERE status='SUPPRESSED'").fetchone()[0]
    sent = conn.execute("SELECT COUNT(*) FROM send_attempts WHERE sent_at IS NOT NULL").fetchone()[0]
    delivered = conn.execute("SELECT COUNT(DISTINCT send_id) FROM message_events WHERE event_type='DELIVERED'").fetchone()[0]
    delivered_email = conn.execute("""SELECT COUNT(DISTINCT e.send_id) FROM message_events e
        JOIN send_attempts s ON s.send_id=e.send_id
        WHERE e.event_type='DELIVERED' AND s.channel='EMAIL'""").fetchone()[0]
    opened = conn.execute("""SELECT COUNT(DISTINCT e.send_id) FROM message_events e
        JOIN send_attempts s ON s.send_id=e.send_id
        WHERE e.event_type='OPENED' AND s.channel='EMAIL'""").fetchone()[0]
    clicked = conn.execute("SELECT COUNT(DISTINCT send_id) FROM message_events WHERE event_type='CLICKED'").fetchone()[0]
    orders = conn.execute("SELECT COUNT(*) FROM orders WHERE order_status IN ('PLACED','PAID')").fetchone()[0]
    attributed = conn.execute("SELECT COUNT(DISTINCT order_id) FROM attributions").fetchone()[0]
    revenue = conn.execute("""SELECT COALESCE(SUM(o.order_total),0) FROM orders o
        WHERE o.order_id IN (SELECT DISTINCT order_id FROM attributions)""").fetchone()[0]
    conn.close()
    return {
        "carts": carts,
        "abandoned_carts": abandoned,
        "abandonment_rate_pct": round(100 * abandoned / carts, 2) if carts else 0,
        "recovered_carts": recovered,
        "recovery_rate_pct": round(100 * recovered / abandoned, 2) if abandoned else 0,
        "send_attempts": sends,
        "suppressed_attempts": suppressed,
        "suppression_rate_pct": round(100 * suppressed / sends, 2) if sends else 0,
        "sent_messages": sent,
        "delivery_rate_pct": round(100 * delivered / sent, 2) if sent else 0,
        "open_rate_pct": round(100 * opened / delivered_email, 2) if delivered_email else 0,
        "click_rate_pct": round(100 * clicked / delivered, 2) if delivered else 0,
        "orders": orders,
        "attributed_orders": attributed,
        "conversion_rate_pct": round(100 * attributed / delivered, 2) if delivered else 0,
        "attributed_revenue": round(revenue, 2),
    }
