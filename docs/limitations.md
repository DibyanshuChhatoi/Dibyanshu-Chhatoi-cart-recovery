# Limitations and Next Steps

- This is a synthetic simulation, not a live email/SMS integration. No real messages are sent.
- The starter implementation uses a simplified deterministic consent and frequency-cap simulation. A production-grade evaluator should apply the consent and cap engines to each candidate using full event history.
- Campaign assignment is synthetic and rule-driven, not optimized by a machine-learning model.
- Attribution uses a simple last eligible click policy; it does not establish causal lift.
- Email open tracking can be unreliable due to privacy features; the generated opens are simulated.
- The schema uses SQLite and floating-point money values for portability and simplicity.
- The initial dashboard is intentionally compact; the CLI pipeline is the primary executable interface.
- A clean baseline run (`--no-anomalies`) should be used to demonstrate baseline integrity, followed by the default anomaly run to demonstrate exception detection.
