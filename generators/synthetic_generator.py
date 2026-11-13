"""Deterministic synthetic e-commerce data generator.

The baseline is generated first. Controlled anomalies are injected only after
the valid baseline has been persisted.
"""
from datetime import datetime, timedelta
from pathlib import Path
import random
import sqlite3

from config import Settings
from database.db import connect, initialize
from engines.business_rules import ConsentRegistry, FrequencyCapTracker

FIRST_NAMES = ["Aarav", "Anaya", "Ishaan", "Diya", "Kabir", "Meera", "Rohan", "Priya", "Arjun", "Sara"]
LAST_NAMES = ["Sharma", "Patel", "Das", "Reddy", "Singh", "Nair", "Kumar", "Gupta", "Rao", "Jain"]
PRODUCTS = [
    ("PRD-001", "Wireless Headphones", 2499.0),
    ("PRD-002", "Smart Watch", 3999.0),
    ("PRD-003", "Laptop Stand", 1299.0),
    ("PRD-004", "Bluetooth Speaker", 1999.0),
    ("PRD-005", "USB-C Hub", 1799.0),
    ("PRD-006", "Mechanical Keyboard", 3499.0),
    ("PRD-007", "Wireless Mouse", 899.0),
    ("PRD-008", "Power Bank", 1499.0),
]
VARIANTS = [("STANDARD", "Your cart is waiting", "You left items in your cart. Continue shopping."),
            ("DISCOUNT", "A little something for you", "Your cart is waiting. Review your items today."),
            ("URGENCY", "Your items may sell out", "Your selected items are still in your cart.")]

def ts(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat()

def generate(settings: Settings):
    settings.validate()
    rng = random.Random(settings.seed)
    initialize(settings.db_path)
    conn = connect(settings.db_path)
    # A fresh generation always starts from an empty database.
    tables = ["attributions","orders","message_events","send_attempts","message_templates",
              "campaigns","cart_update_events","cart_lines","carts","sessions","consents","customers"]
    with conn:
        for table in tables:
            conn.execute(f"DELETE FROM {table}")

        start = datetime.fromisoformat(settings.simulation_start)
        customer_count = max(10, (settings.carts + 9) // 10)
        customer_ids = [f"CUS-{i:06d}" for i in range(1, customer_count + 1)]

        # 1. Master customers.
        for i, cid in enumerate(customer_ids, 1):
            first = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
            last = LAST_NAMES[((i - 1) // len(FIRST_NAMES)) % len(LAST_NAMES)]
            conn.execute("""INSERT INTO customers VALUES (?,?,?,?,?,?,?)""",
                (cid, first, last, f"customer{i:06d}@example.test",
                 f"+1555{i:07d}", "IN", ts(start - timedelta(days=rng.randint(1, 365)))))

        # 2. Consent history: two channels per customer; status is effective at simulation start.
        for i, cid in enumerate(customer_ids, 1):
            for channel, offset in (("EMAIL", 0), ("SMS", 1)):
                roll = (i * 7 + offset * 13) % 100
                status = "GRANTED" if roll < 78 else ("DENIED" if roll < 91 else "WITHDRAWN")
                effective = start - timedelta(days=30)
                conn.execute("INSERT INTO consents VALUES (?,?,?,?,?,?,?)",
                    (f"CON-{i:06d}-{offset+1}", cid, channel, status, ts(effective), None, "SYNTHETIC_SIGNUP"))

        # Load consent history once and maintain rolling send caps in memory for scalable evaluation.
        consent_registry = ConsentRegistry(conn)
        cap_tracker = FrequencyCapTracker()

        # 3. Campaigns and templates.
        campaign_rows = []
        campaign_count = 6
        for i in range(1, campaign_count + 1):
            channel = "EMAIL" if i % 2 else "SMS"
            variant, subject, body = VARIANTS[(i - 1) % len(VARIANTS)]
            campaign_id = f"CMP-2026-{i:06d}"
            campaign_rows.append((campaign_id, f"Cart Recovery {variant}", channel, variant, ts(start), "ACTIVE"))
        conn.executemany("INSERT INTO campaigns VALUES (?,?,?,?,?,?)", campaign_rows)

        cart_meta = {}
        # 4. Sessions, carts and cart lines.
        simulation_as_of = start + timedelta(days=31)
        for i in range(1, settings.carts + 1):
            cart_id = f"CART-2026-{i:06d}"
            # Ten carts per customer creates realistic repeated contact history and cap conflicts.
            cid = customer_ids[(i - 1) // 10]
            session_id = f"SES-{i:06d}"
            if i <= settings.abandoned_carts:
                # Older last activity: inactivity rule will classify these as abandoned.
                last_activity = start + timedelta(days=10, minutes=i)
            else:
                # Recent last activity: these remain active at the fixed evaluation timestamp.
                last_activity = simulation_as_of - timedelta(minutes=rng.randint(1, 45))
            created = last_activity - timedelta(minutes=30)
            is_abandoned = (simulation_as_of - last_activity) >= timedelta(minutes=settings.inactivity_minutes)
            abandoned_at = last_activity + timedelta(minutes=settings.inactivity_minutes) if is_abandoned else None

            # Non-abandoned carts are a deterministic mix of active and purchased.
            initial_status = "ABANDONED" if is_abandoned else ("PURCHASED" if i % 5 == 0 else "ACTIVE")
            device = ["MOBILE", "DESKTOP", "TABLET"][i % 3]
            conn.execute("INSERT INTO sessions VALUES (?,?,?,?,?,?)",
                (session_id, cid, device, ["DIRECT","SEARCH","SOCIAL","EMAIL"][i % 4], ts(created), ts(last_activity)))
            conn.execute("INSERT INTO carts VALUES (?,?,?,?,?,?,?,?)",
                (cart_id, cid, session_id, ts(created), ts(last_activity),
                 ts(abandoned_at) if abandoned_at else None, initial_status, 0.0))

            line_count = 1 + (i % 3)
            cart_total = 0.0
            line_ids = []
            quantity_update = (i % 7 == 0)
            first_old_quantity = None
            for j in range(1, line_count + 1):
                product_id, product_name, price = PRODUCTS[(i + j) % len(PRODUCTS)]
                initial_quantity = 1 + ((i + j) % 2)
                quantity = initial_quantity + (1 if quantity_update and j == 1 else 0)
                if j == 1:
                    first_old_quantity = initial_quantity
                line_total = round(quantity * price, 2)
                cart_total += line_total
                line_id = f"LINE-{i:06d}-{j:02d}"
                line_ids.append(line_id)
                conn.execute("INSERT INTO cart_lines VALUES (?,?,?,?,?,?,?)",
                    (line_id, cart_id, product_id, product_name, quantity, price, line_total))
                event_time = created + timedelta(minutes=5 * j)
                if j == line_count and not quantity_update:
                    event_time = last_activity
                conn.execute("INSERT INTO cart_update_events VALUES (?,?,?,?,?,?,?)",
                    (f"UPD-{i:06d}-{j:02d}", cart_id, "ADD_ITEM", ts(event_time),
                     line_id, None, initial_quantity))
            if quantity_update:
                conn.execute("INSERT INTO cart_update_events VALUES (?,?,?,?,?,?,?)",
                    (f"UPD-{i:06d}-Q01", cart_id, "UPDATE_QUANTITY", ts(last_activity),
                     line_ids[0], first_old_quantity, first_old_quantity + 1))
            conn.execute("UPDATE carts SET cart_total=? WHERE cart_id=?", (round(cart_total, 2), cart_id))
            cart_meta[cart_id] = {"customer_id": cid, "abandoned": is_abandoned, "status": initial_status,
                                  "last_activity": last_activity, "abandoned_at": abandoned_at,
                                  "total": round(cart_total, 2), "line_ids": line_ids}

        # 5. Create exactly the configured number of send attempts against abandoned carts.
        # Suppressed attempts are retained as decisions; no actual send event is emitted for them.
        send_meta = {}
        for i in range(1, settings.send_attempts + 1):
            cart_id = f"CART-2026-{i:06d}"
            meta = cart_meta[cart_id]
            cid = meta["customer_id"]
            channel = "EMAIL" if i % 2 else "SMS"
            campaign_index = (i - 1) % campaign_count
            campaign_id = f"CMP-2026-{campaign_index+1:06d}"
            template_id = f"MSG-{cart_id}-01"
            scheduled = (meta["abandoned_at"] or meta["last_activity"]) + timedelta(minutes=5)
            # Evaluate effective-dated consent and rolling cap against persisted send history.
            consent = consent_registry.status_at(cid, channel, ts(scheduled))
            channel_cap = settings.email_cap if channel == "EMAIL" else settings.sms_cap
            cap_conflict = cap_tracker.reached(
                cid, channel, ts(scheduled), channel_cap, settings.cap_window_days
            )
            if consent != "GRANTED":
                status, reason, sent_at = "SUPPRESSED", f"CONSENT_{consent}", None
            elif cap_conflict:
                status, reason, sent_at = "SUPPRESSED", "FREQUENCY_CAP", None
            else:
                status, reason, sent_at = "SENT", None, scheduled + timedelta(seconds=30)
                cap_tracker.record(cid, channel, ts(sent_at))
            send_id = f"SEND-2026-{i:06d}"
            variant, subject, body = VARIANTS[campaign_index % len(VARIANTS)]
            conn.execute("INSERT INTO message_templates VALUES (?,?,?,?,?,?)",
                (template_id, campaign_id, f"{variant} Cart Template", subject if channel == "EMAIL" else None, body, variant))
            conn.execute("INSERT INTO send_attempts VALUES (?,?,?,?,?,?,?,?,?,?)",
                (send_id, cart_id, cid, campaign_id, template_id, channel, ts(scheduled),
                 ts(sent_at) if sent_at else None, status, reason))
            send_meta[send_id] = {"cart_id": cart_id, "customer_id": cid, "campaign_id": campaign_id,
                                  "channel": channel, "status": status, "sent_at": sent_at}

            if status == "SENT":
                events = [("SENT", sent_at)]
                if i % 10 != 0:
                    events.append(("DELIVERED", sent_at + timedelta(seconds=10)))
                    if channel == "EMAIL" and i % 4 == 1:
                        events.append(("OPENED", sent_at + timedelta(minutes=2)))
                    if i % 6 == 0 or (channel == "EMAIL" and i % 6 == 3):
                        events.append(("CLICKED", sent_at + timedelta(minutes=3)))
                else:
                    events.append(("BOUNCED", sent_at + timedelta(seconds=10)))
                for j, (event_type, event_time) in enumerate(events, 1):
                    conn.execute("INSERT INTO message_events VALUES (?,?,?,?)",
                        (f"EVT-{i:06d}-{j:02d}", send_id, event_type, ts(event_time)))
                if any(event_type == "DELIVERED" for event_type, _ in events):
                    conn.execute("UPDATE send_attempts SET status='DELIVERED' WHERE send_id=?", (send_id,))
                elif any(event_type == "BOUNCED" for event_type, _ in events):
                    conn.execute("UPDATE send_attempts SET status='FAILED' WHERE send_id=?", (send_id,))

        # 6. Orders: deterministic subset of carts. Some are post-abandonment recoveries.
        order_meta = {}
        order_counter = 0
        for i in range(1, settings.carts + 1):
            should_order = (i % 5 == 0) or (i <= settings.abandoned_carts and i % 7 == 0)
            if not should_order:
                continue
            cart_id = f"CART-2026-{i:06d}"
            meta = cart_meta[cart_id]
            order_counter += 1
            order_id = f"ORD-2026-{order_counter:06d}"
            base_time = meta["abandoned_at"] if meta["abandoned"] else meta["last_activity"]
            order_time = base_time + timedelta(days=(i % 10), hours=1)
            order_status = "CANCELLED" if i % 50 == 0 else ("REFUNDED" if i % 40 == 0 else ("PLACED" if i % 10 == 0 else "PAID"))
            conn.execute("INSERT INTO orders VALUES (?,?,?,?,?,?)",
                (order_id, meta["customer_id"], cart_id, ts(order_time), meta["total"], order_status))
            order_meta[order_id] = {"cart_id": cart_id, "order_time": order_time,
                                   "total": meta["total"], "order_status": order_status}
            if order_status in ("PAID", "PLACED"):
                if meta["abandoned"]:
                    # A qualifying purchase after abandonment is a recovery; history is retained.
                    conn.execute("UPDATE carts SET status='RECOVERED' WHERE cart_id=?", (cart_id,))
                else:
                    conn.execute("UPDATE carts SET status='PURCHASED' WHERE cart_id=?", (cart_id,))

        # Ensure the starter dataset demonstrates at least one end-to-end attributed recovery
        # whenever at least one real send exists. This is deterministic, not a random label.
        qualifying = conn.execute("""SELECT s.send_id,s.cart_id,s.customer_id,s.campaign_id,s.sent_at
            FROM send_attempts s WHERE s.sent_at IS NOT NULL ORDER BY s.send_id LIMIT 1""").fetchone()
        if qualifying:
            click_exists = conn.execute("SELECT 1 FROM message_events WHERE send_id=? AND event_type='CLICKED'",
                                        (qualifying["send_id"],)).fetchone()
            click_time = datetime.fromisoformat(qualifying["sent_at"]) + timedelta(minutes=3)
            if not click_exists:
                conn.execute("INSERT INTO message_events VALUES (?,?,?,?)",
                    ("EVT-RECOVERY-CLICK", qualifying["send_id"], "CLICKED", ts(click_time)))
            existing_order = conn.execute("SELECT order_date FROM orders WHERE cart_id=? ORDER BY order_date LIMIT 1",
                                           (qualifying["cart_id"],)).fetchone()
            if not existing_order:
                next_order = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] + 1
                cart_total = conn.execute("SELECT cart_total FROM carts WHERE cart_id=?",
                                          (qualifying["cart_id"],)).fetchone()[0]
                recovery_order_time = click_time + timedelta(days=1)
                conn.execute("INSERT INTO orders VALUES (?,?,?,?,?,?)",
                    (f"ORD-2026-{next_order:06d}", qualifying["customer_id"], qualifying["cart_id"],
                     ts(recovery_order_time), cart_total, "PAID"))
                conn.execute("UPDATE carts SET status='RECOVERED' WHERE cart_id=?", (qualifying["cart_id"],))
                order_meta[f"ORD-2026-{next_order:06d}"] = {
                    "cart_id": qualifying["cart_id"], "order_time": recovery_order_time,
                    "total": cart_total, "order_status": "PAID"
                }
                order_counter = next_order

        # 7. Attribution: index send attempts by cart to avoid an O(orders × sends) scan.
        sends_by_cart = {}
        for send_id, sm in send_meta.items():
            sends_by_cart.setdefault(sm["cart_id"], []).append((send_id, sm))
        attr_counter = 0
        for order_id, om in order_meta.items():
            if om.get("order_status", "PAID") not in ("PAID", "PLACED"):
                continue
            candidates = []
            for send_id, sm in sends_by_cart.get(om["cart_id"], []):
                if sm["status"] != "SENT":
                    continue
                click = conn.execute("""SELECT event_time FROM message_events
                    WHERE send_id=? AND event_type='CLICKED' ORDER BY event_time DESC LIMIT 1""",
                    (send_id,)).fetchone()
                if click:
                    click_time = datetime.fromisoformat(click["event_time"])
                    delta = om["order_time"] - click_time
                    if timedelta(0) <= delta <= timedelta(days=settings.attribution_days):
                        candidates.append((click_time, send_id, sm["campaign_id"]))
            if candidates:
                _, send_id, campaign_id = sorted(candidates, reverse=True)[0]
                attr_counter += 1
                conn.execute("INSERT INTO attributions VALUES (?,?,?,?,?,?,?,?)",
                    (f"ATTR-{attr_counter:06d}", order_id, campaign_id, send_id,
                     ts(om["order_time"]), settings.attribution_days, "LAST_ELIGIBLE_CLICK", 1.0))

    conn.close()
    return {"customers": customer_count, "carts": settings.carts,
            "abandoned_carts": settings.abandoned_carts, "send_attempts": settings.send_attempts,
            "orders": order_counter, "database": settings.db_path}
