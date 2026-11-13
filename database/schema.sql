PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL UNIQUE,
    country TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consents (
    consent_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    channel TEXT NOT NULL CHECK(channel IN ('EMAIL','SMS')),
    status TEXT NOT NULL CHECK(status IN ('GRANTED','DENIED','WITHDRAWN')),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    source TEXT NOT NULL,
    CHECK(effective_to IS NULL OR effective_to > effective_from)
);

CREATE INDEX IF NOT EXISTS idx_consent_customer_channel_time
ON consents(customer_id, channel, effective_from);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    device_type TEXT NOT NULL CHECK(device_type IN ('MOBILE','DESKTOP','TABLET')),
    source TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS carts (
    cart_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    created_at TEXT NOT NULL,
    last_activity_at TEXT NOT NULL,
    abandoned_at TEXT,
    status TEXT NOT NULL CHECK(status IN ('ACTIVE','ABANDONED','RECOVERED','PURCHASED')),
    cart_total REAL NOT NULL CHECK(cart_total >= 0)
);

CREATE INDEX IF NOT EXISTS idx_carts_status ON carts(status);

CREATE TABLE IF NOT EXISTS cart_lines (
    cart_line_id TEXT PRIMARY KEY,
    cart_id TEXT NOT NULL REFERENCES carts(cart_id),
    product_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price REAL NOT NULL CHECK(unit_price >= 0),
    line_total REAL NOT NULL CHECK(line_total >= 0)
);

CREATE INDEX IF NOT EXISTS idx_cart_lines_cart ON cart_lines(cart_id);

CREATE TABLE IF NOT EXISTS cart_update_events (
    update_id TEXT PRIMARY KEY,
    cart_id TEXT NOT NULL REFERENCES carts(cart_id),
    action TEXT NOT NULL CHECK(action IN ('ADD_ITEM','UPDATE_QUANTITY','REMOVE_ITEM')),
    event_time TEXT NOT NULL,
    cart_line_id TEXT REFERENCES cart_lines(cart_line_id),
    old_quantity INTEGER,
    new_quantity INTEGER
);

CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id TEXT PRIMARY KEY,
    campaign_name TEXT NOT NULL,
    channel TEXT NOT NULL CHECK(channel IN ('EMAIL','SMS')),
    variant TEXT NOT NULL,
    scheduled_at TEXT NOT NULL,
    active_status TEXT NOT NULL CHECK(active_status IN ('ACTIVE','INACTIVE'))
);

CREATE TABLE IF NOT EXISTS message_templates (
    template_id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(campaign_id),
    template_name TEXT NOT NULL,
    subject TEXT,
    body TEXT NOT NULL,
    variant_code TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS send_attempts (
    send_id TEXT PRIMARY KEY,
    cart_id TEXT NOT NULL REFERENCES carts(cart_id),
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    campaign_id TEXT NOT NULL REFERENCES campaigns(campaign_id),
    template_id TEXT NOT NULL REFERENCES message_templates(template_id),
    channel TEXT NOT NULL CHECK(channel IN ('EMAIL','SMS')),
    scheduled_at TEXT NOT NULL,
    sent_at TEXT,
    status TEXT NOT NULL CHECK(status IN ('SCHEDULED','SENT','DELIVERED','FAILED','SUPPRESSED')),
    suppression_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_send_customer_channel_time
ON send_attempts(customer_id, channel, sent_at);

CREATE TABLE IF NOT EXISTS message_events (
    event_id TEXT PRIMARY KEY,
    send_id TEXT NOT NULL REFERENCES send_attempts(send_id),
    event_type TEXT NOT NULL CHECK(event_type IN ('SENT','DELIVERED','OPENED','CLICKED','BOUNCED','FAILED')),
    event_time TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    cart_id TEXT NOT NULL REFERENCES carts(cart_id),
    order_date TEXT NOT NULL,
    order_total REAL NOT NULL CHECK(order_total >= 0),
    order_status TEXT NOT NULL CHECK(order_status IN ('PLACED','PAID','CANCELLED','REFUNDED'))
);

CREATE TABLE IF NOT EXISTS attributions (
    attribution_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(order_id),
    campaign_id TEXT NOT NULL REFERENCES campaigns(campaign_id),
    send_id TEXT NOT NULL REFERENCES send_attempts(send_id),
    attributed_at TEXT NOT NULL,
    attribution_window_days INTEGER NOT NULL,
    attribution_type TEXT NOT NULL,
    credit REAL NOT NULL CHECK(credit > 0 AND credit <= 1)
);

CREATE INDEX IF NOT EXISTS idx_attribution_order ON attributions(order_id);
