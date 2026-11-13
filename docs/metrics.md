# Metric Definitions

Metrics are computed from persisted source/event records, not assigned independently.

| Metric | Definition | Notes |
|---|---|---|
| Cart abandonment rate | Carts with non-null `abandoned_at` / all carts | The anomaly-injected output includes one deliberately invalid extra abandoned cart; the clean baseline has exactly the configured 40%. |
| Recovery rate | Carts in RECOVERED status / carts with non-null `abandoned_at` | Recovery requires a qualifying PAID or PLACED order after abandonment. |
| Suppression rate | SUPPRESSED send attempts / all send attempts | Includes consent and frequency-cap suppression. |
| Delivery rate | Distinct DELIVERED sends / sends with non-null `sent_at` | Sent messages can bounce. |
| Email open rate | Distinct OPENED email sends / distinct DELIVERED email sends | SMS is excluded because open tracking is not modeled for SMS. |
| Click rate | Distinct CLICKED sends / distinct DELIVERED sends | Clicks are simulated for email and SMS. |
| Attributed conversion rate | Distinct attributed orders / delivered sends | Uses last eligible recovery click within the seven-day window. |
| Attributed revenue | Sum of order totals for distinct attributed orders | Only PAID/PLACED orders can receive attribution. |

These are simulated operational metrics, not causal estimates of incremental campaign lift. A holdout/control experiment would be required to estimate causal lift.
