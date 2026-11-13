# Architecture

The project is a locally executable Python pipeline with an optional Streamlit presentation layer.

```text
CLI (main.py)
   |
   +--> Synthetic generator --> SQLite master and transaction tables
   |
   +--> Anomaly injector -----> Ground-truth CSV (separate)
   |
   +--> Validator ------------> Validation JSON
   |
   +--> Exporter -------------> CSV exports + source manifest
   |
   +--> Metrics --------------> Analytics JSON
                                  |
                                  v
                           Streamlit dashboard
```

The generator, validator and metrics can run without Streamlit. SQLite is the source of truth; CSV and JSON are portable exports.

## Processing order

1. Customers and effective-dated consent.
2. Sessions.
3. Carts and cart lines.
4. Campaigns and templates.
5. Send attempts and message events.
6. Orders.
7. Attribution.
8. Controlled anomaly injection.
9. Validation, exports and analytics.

The pipeline uses a fixed Python `random.Random(seed)` instance. Simulation timestamps are anchored to a fixed start date rather than wall-clock time, so generated business records can be reproducible.
