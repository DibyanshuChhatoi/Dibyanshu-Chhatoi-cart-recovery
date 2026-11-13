# Data Dictionary

All IDs are immutable strings. Timestamps use ISO-8601 simulation-local time (`YYYY-MM-DDTHH:MM:SS`). Currency values are synthetic INR-like amounts stored as SQLite REAL for this portable exercise. Synthetic contact details are not routable.

## Customer

| Field | Type | Required | Allowed values / unit | Unique | Validation |
|---|---|---|---|---|---|
| customer_id | TEXT | Yes | `CUS-` + six digits | Yes (PK) | Must match deterministic ID pattern |
| first_name | TEXT | Yes | Synthetic name | No | Non-empty |
| last_name | TEXT | Yes | Synthetic name | No | Non-empty |
| email | TEXT | Yes | `.example.test` | Yes | Non-empty; reserved test domain |
| phone | TEXT | Yes | Synthetic phone string | Yes | Non-empty |
| country | TEXT | Yes | ISO-like country code | No | Non-empty |
| created_at | TEXT | Yes | ISO timestamp | No | Valid timestamp |

## Consent

| Field | Type | Required | Allowed values / unit | Unique | Validation |
|---|---|---|---|---|---|
| consent_id | TEXT | Yes | `CON-...` | Yes (PK) | Unique |
| customer_id | TEXT | Yes | Existing customer ID | No | FK to Customer |
| channel | TEXT | Yes | EMAIL, SMS | No | Enum check |
| status | TEXT | Yes | GRANTED, DENIED, WITHDRAWN | No | Enum check |
| effective_from | TEXT | Yes | ISO timestamp | No | Valid timestamp |
| effective_to | TEXT | No | ISO timestamp or null | No | Must be later than effective_from; exclusive end |
| source | TEXT | Yes | Synthetic provenance label | No | Non-empty |

## Session

| Field | Type | Required | Allowed values / unit | Unique | Validation |
|---|---|---|---|---|---|
| session_id | TEXT | Yes | `SES-` + six digits | Yes (PK) | Unique |
| customer_id | TEXT | Yes | Existing customer ID | No | FK to Customer |
| device_type | TEXT | Yes | MOBILE, DESKTOP, TABLET | No | Enum check |
| source | TEXT | Yes | DIRECT, SEARCH, SOCIAL, EMAIL | No | Non-empty |
| started_at | TEXT | Yes | ISO timestamp | No | Valid timestamp |
| ended_at | TEXT | No | ISO timestamp or null | No | Must not precede start |

## Cart

| Field | Type | Required | Allowed values / unit | Unique | Validation |
|---|---|---|---|---|---|
| cart_id | TEXT | Yes | `CART-2026-` + six digits | Yes (PK) | Unique deterministic ID |
| customer_id | TEXT | Yes | Existing customer ID | No | FK to Customer |
| session_id | TEXT | Yes | Existing session ID | No | FK to Session |
| created_at | TEXT | Yes | ISO timestamp | No | Valid timestamp |
| last_activity_at | TEXT | Yes | ISO timestamp | No | Must be >= created_at |
| abandoned_at | TEXT | No | ISO timestamp or null | No | Derived from last activity + inactivity threshold |
| status | TEXT | Yes | ACTIVE, ABANDONED, RECOVERED, PURCHASED | No | Enum and lifecycle validation |
| cart_total | REAL | Yes | Currency units | No | >= 0; must equal sum of cart line totals in clean data |

## CartLine

| Field | Type | Required | Allowed values / unit | Unique | Validation |
|---|---|---|---|---|---|
| cart_line_id | TEXT | Yes | `LINE-...` | Yes (PK) | Unique |
| cart_id | TEXT | Yes | Existing cart ID | No | FK to Cart |
| product_id | TEXT | Yes | Synthetic product ID | No | Non-empty |
| product_name | TEXT | Yes | Synthetic product name | No | Non-empty |
| quantity | INTEGER | Yes | Positive units | No | > 0 |
| unit_price | REAL | Yes | Currency units | No | >= 0 |
| line_total | REAL | Yes | Currency units | No | Must equal quantity × unit_price |

## Campaign

| Field | Type | Required | Allowed values / unit | Unique | Validation |
|---|---|---|---|---|---|
| campaign_id | TEXT | Yes | `CMP-2026-` + six digits | Yes (PK) | Unique deterministic ID |
| campaign_name | TEXT | Yes | Descriptive name | No | Non-empty |
| channel | TEXT | Yes | EMAIL, SMS | No | Enum check |
| variant | TEXT | Yes | STANDARD, DISCOUNT, URGENCY | No | Enum-like controlled value |
| scheduled_at | TEXT | Yes | ISO timestamp | No | Valid timestamp |
| active_status | TEXT | Yes | ACTIVE, INACTIVE | No | Enum check |

## MessageTemplate

| Field | Type | Required | Allowed values / unit | Unique | Validation |
|---|---|---|---|---|---|
| template_id | TEXT | Yes | `MSG-<cart-id>-01` | Yes (PK) | Deterministic ID derived from cart ID |
| campaign_id | TEXT | Yes | Existing campaign ID | No | FK to Campaign |
| template_name | TEXT | Yes | Descriptive name | No | Non-empty |
| subject | TEXT | No | Email subject; null for SMS | No | Optional |
| body | TEXT | Yes | Synthetic message body | No | Non-empty |
| variant_code | TEXT | Yes | STANDARD, DISCOUNT, URGENCY | No | Matches campaign variant |

## SendAttempt

| Field | Type | Required | Allowed values / unit | Unique | Validation |
|---|---|---|---|---|---|
| send_id | TEXT | Yes | `SEND-2026-` + six digits | Yes (PK) | Unique deterministic ID |
| cart_id | TEXT | Yes | Existing cart ID | No | FK to Cart |
| customer_id | TEXT | Yes | Existing customer ID | No | FK to Customer |
| campaign_id | TEXT | Yes | Existing campaign ID | No | FK to Campaign |
| template_id | TEXT | Yes | Existing template ID | No | FK to MessageTemplate |
| channel | TEXT | Yes | EMAIL, SMS | No | Enum; must match campaign |
| scheduled_at | TEXT | Yes | ISO timestamp | No | Valid timestamp |
| sent_at | TEXT | No | ISO timestamp or null | No | Null for suppressed attempts |
| status | TEXT | Yes | SCHEDULED, SENT, DELIVERED, FAILED, SUPPRESSED | No | Enum check |
| suppression_reason | TEXT | No | Consent/cap reason or null | No | Required when SUPPRESSED |

## Order

| Field | Type | Required | Allowed values / unit | Unique | Validation |
|---|---|---|---|---|---|
| order_id | TEXT | Yes | `ORD-2026-` + six digits | Yes (PK) | Unique deterministic ID |
| customer_id | TEXT | Yes | Existing customer ID | No | FK to Customer |
| cart_id | TEXT | Yes | Existing cart ID | No | FK to Cart |
| order_date | TEXT | Yes | ISO timestamp | No | Valid timestamp |
| order_total | REAL | Yes | Currency units | No | >= 0; reconciles to cart total in this simulation |
| order_status | TEXT | Yes | PLACED, PAID, CANCELLED, REFUNDED | No | Enum check |

## Attribution

| Field | Type | Required | Allowed values / unit | Unique | Validation |
|---|---|---|---|---|---|
| attribution_id | TEXT | Yes | `ATTR-` + six digits | Yes (PK) | Unique |
| order_id | TEXT | Yes | Existing order ID | No | FK to Order |
| campaign_id | TEXT | Yes | Existing campaign ID | No | FK to Campaign |
| send_id | TEXT | Yes | Existing send ID | No | FK to SendAttempt |
| attributed_at | TEXT | Yes | ISO timestamp | No | Usually order time |
| attribution_window_days | INTEGER | Yes | Days | No | Positive; default 7 |
| attribution_type | TEXT | Yes | LAST_ELIGIBLE_CLICK | No | Documented model |
| credit | REAL | Yes | Fraction (0,1] | No | Positive and <= 1; clean data has one full credit per order |

## Supporting event entities

- `MessageEvent`: `event_id` PK, `send_id` FK, `event_type` (SENT/DELIVERED/OPENED/CLICKED/BOUNCED/FAILED), `event_time` ISO timestamp.
- `CartUpdateEvent`: `update_id` PK, `cart_id` FK, action (ADD_ITEM/UPDATE_QUANTITY/REMOVE_ITEM), event timestamp, optional cart line FK and old/new quantities.

## Relationships and cardinality

- Customer 1:N Consent, Session, Cart, Order, SendAttempt.
- Session 1:N Cart.
- Cart 1:N CartLine, CartUpdateEvent, SendAttempt, and potentially Order.
- Campaign 1:N MessageTemplate, SendAttempt, Attribution.
- MessageTemplate 1:N SendAttempt.
- SendAttempt 1:N MessageEvent and 0:N Attribution.
- Order 1:N raw Attribution rows; clean last-click policy expects at most one credited campaign per order.
- Cart and Campaign are N:M through SendAttempt; Order and Campaign are N:M through Attribution.

Consent is effective-dated. `effective_to` is exclusive. The effective record is the latest row where `effective_from <= event_time < effective_to`, or no end time exists. Missing consent is treated as denied.

## Production considerations

This is a synthetic challenge implementation. A production system should use timezone-aware UTC timestamps, decimal money types, product master data, consent evidence and source metadata, transactional message queues, and stronger event idempotency.
