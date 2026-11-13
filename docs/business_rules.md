# Business Rules and Assumptions

These are explicit starter assumptions because the assignment does not prescribe exact thresholds.

1. A cart is considered abandoned after 60 minutes without cart activity, if it has not already been purchased at that decision time.
2. Abandonment is a derived timestamp: `last_activity_at + inactivity_minutes`.
3. A message candidate is evaluated against the latest consent record effective at the scheduled/send time for the chosen channel.
4. A missing consent record is treated as DENIED (fail closed).
5. Email and SMS are evaluated independently.
6. Frequency caps default to 2 messages per channel in a rolling 7-day window. Suppressed attempts are recorded and do not count as sends.
7. Recovery campaign attribution uses last eligible recovery click before purchase, within 7 days. A purchase without a qualifying click receives no click-based attribution.
8. One order can receive at most one campaign credit in the clean baseline. Injected duplicate attribution is an intentional negative case.
9. Events are append-only in the event tables. The current cart status is a projection; the update history remains available.
10. Synthetic customer contact details use reserved `.test` email addresses and non-routable example phone patterns.

## Edge cases

- MESSAGE_AFTER_OPTOUT: a withdrawal becomes effective before a message's sent_at.
- ABANDONED_AFTER_PURCHASE: abandoned_at is later than order_date.
- DOUBLE_ATTRIBUTION: more than one attribution row credits the same order.
- STALE_CART_TOTAL: cart header total differs from sum of its cart-line totals.

The anomaly injector runs after valid baseline generation and records expected labels separately in `data/ground_truth/ground_truth.csv`.

## Synthetic evaluation timestamp and volume shaping

The generator uses a fixed evaluation timestamp 31 days after the simulation start. It places the configured abandoned cohort's last activity sufficiently far before that timestamp, and the remaining cohort's last activity within the configured inactivity threshold. The `abandoned_at` field is calculated from `last_activity_at + inactivity_minutes`; the abandoned label is derived by comparing the activity timestamp with the fixed evaluation timestamp. This makes the 40% target reproducible without independently assigning an outcome label.

Ten carts are assigned per synthetic customer (where volume permits) so repeated contact history and rolling frequency caps can be evaluated. The cap is enforced from previously persisted actual sends, separately for EMAIL and SMS. Suppressed attempts do not count as sends.

Order statuses include a deterministic mix of PAID, PLACED, CANCELLED and REFUNDED. Only PAID and PLACED orders count as conversions or qualify for attribution.

Email open events are generated only for email messages. Click events can occur for either channel. Bounced messages receive a BOUNCED event and FAILED send status.
