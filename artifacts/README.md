# Full Synthetic Dataset Artifact

`full_dataset.zip` contains the full deterministic dataset generated with seed `20261022` and configuration `50,000 carts / 20,000 baseline abandoned carts / 10,000 send attempts`.

Contents include per-entity CSV and JSON exports, `seed_data.sql`, `source_manifest.json`, the separate `ground_truth.csv`, `validation_report.json`, and `analytics_summary.json`.

The final anomaly-injected dataset reports 20,001 carts with an `abandoned_at` value because one required negative scenario deliberately marks a previously purchased cart as abandoned. The clean baseline before anomaly injection contains exactly 20,000 abandoned carts.

All records are synthetic. No real customer information or messages are used.
