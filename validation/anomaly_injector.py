"""Inject four labelled anomalies after a valid baseline has been generated."""
from datetime import datetime, timedelta
import csv
from pathlib import Path

def inject(db_path: str, ground_truth_path: str):
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    anomalies = []

    # 1. Sent after opt-out: choose an actual sent attempt and backdate withdrawal.
    sent = conn.execute("""SELECT s.send_id,s.customer_id,s.channel,s.sent_at
        FROM send_attempts s
        WHERE s.sent_at IS NOT NULL AND s.sent_at=(
          SELECT MAX(x.sent_at) FROM send_attempts x
          WHERE x.customer_id=s.customer_id AND x.channel=s.channel AND x.sent_at IS NOT NULL
        ) ORDER BY s.send_id LIMIT 1""").fetchone()
    if sent:
        consent_id = f"CON-ANOM-001"
        withdrawal = (datetime.fromisoformat(sent["sent_at"]) - timedelta(minutes=1)).isoformat()
        conn.execute("UPDATE consents SET effective_to=? WHERE customer_id=? AND channel=? AND effective_to IS NULL AND effective_from<?",
            (withdrawal, sent["customer_id"], sent["channel"], withdrawal))
        conn.execute("INSERT INTO consents VALUES (?,?,?,?,?,?,?)",
            (consent_id, sent["customer_id"], sent["channel"], "WITHDRAWN", withdrawal, None, "INJECTED_ANOMALY"))
        anomalies.append(("AN-001","MESSAGE_AFTER_OPTOUT",sent["send_id"],"INVALID",
                          "A withdrawal is effective before the actual send timestamp."))

    # 2. Cart marked abandoned after its purchase.
    purchased = conn.execute("""SELECT o.cart_id,o.order_date FROM orders o
        JOIN carts c ON c.cart_id=o.cart_id WHERE c.abandoned_at IS NULL
        ORDER BY o.order_id LIMIT 1""").fetchone()
    if purchased:
        wrong_time = (datetime.fromisoformat(purchased["order_date"]) + timedelta(minutes=10)).isoformat()
        conn.execute("UPDATE carts SET status='ABANDONED', abandoned_at=? WHERE cart_id=?",
                     (wrong_time, purchased["cart_id"]))
        anomalies.append(("AN-002","ABANDONED_AFTER_PURCHASE",purchased["cart_id"],"INVALID",
                          "The cart abandonment timestamp occurs after its purchase."))

    # 3. Duplicate attribution: add second campaign credit for an already attributed order.
    attr = conn.execute("SELECT order_id,send_id,attributed_at,attribution_window_days FROM attributions ORDER BY attribution_id LIMIT 1").fetchone()
    if attr:
        send = conn.execute("SELECT campaign_id FROM send_attempts WHERE send_id=?", (attr["send_id"],)).fetchone()
        other = conn.execute("SELECT campaign_id FROM campaigns WHERE campaign_id<>? ORDER BY campaign_id LIMIT 1",
                             (send["campaign_id"],)).fetchone()
        if other:
            next_id = conn.execute("SELECT COUNT(*) FROM attributions").fetchone()[0] + 1
            conn.execute("INSERT INTO attributions VALUES (?,?,?,?,?,?,?,?)",
                (f"ATTR-{next_id:06d}", attr["order_id"], other["campaign_id"], attr["send_id"],
                 attr["attributed_at"], attr["attribution_window_days"], "INJECTED_DUPLICATE", 1.0))
            anomalies.append(("AN-003","DOUBLE_ATTRIBUTION",attr["order_id"],"INVALID",
                              "One order has more than one campaign credit."))

    # 4. Stale cart total: change quantity and line total but deliberately do not update cart total.
    line = conn.execute("""SELECT cl.cart_line_id,cl.cart_id,cl.quantity,cl.unit_price,c.last_activity_at
        FROM cart_lines cl JOIN carts c ON c.cart_id=cl.cart_id
        ORDER BY cl.cart_line_id LIMIT 1""").fetchone()
    if line:
        new_qty = line["quantity"] + 1
        conn.execute("UPDATE cart_lines SET quantity=?, line_total=? WHERE cart_line_id=?",
                     (new_qty, round(new_qty * line["unit_price"], 2), line["cart_line_id"]))
        conn.execute("INSERT INTO cart_update_events VALUES (?,?,?,?,?,?,?)",
            ("UPD-ANOM-004", line["cart_id"], "UPDATE_QUANTITY",
             (datetime.fromisoformat(line["last_activity_at"]) + timedelta(minutes=1)).isoformat(),
             line["cart_line_id"], line["quantity"], new_qty))
        anomalies.append(("AN-004","STALE_CART_TOTAL",line["cart_id"],"INVALID",
                          "Cart line quantity changed but the cart header total was not recalculated."))

    conn.commit()
    conn.close()
    Path(ground_truth_path).parent.mkdir(parents=True, exist_ok=True)
    with open(ground_truth_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["anomaly_id","issue_type","affected_id","ground_truth","description"])
        writer.writerows(anomalies)
    return anomalies
