# Testing and Verification

## Starter run

```bash
python main.py --carts 1000 --abandoned 400 --sends 200 --seed 20261022
```

Expected baseline volume before anomaly injection:
- carts: 1,000
- abandoned carts: 400
- send attempts: 200

The default pipeline injects four controlled anomalies after the valid baseline. Therefore, the final anomaly-injected export reports 401 carts with `abandoned_at`: the 400 baseline abandoned carts plus the deliberately invalid post-purchase abandonment case.

## Clean baseline

```bash
python main.py --carts 1000 --abandoned 400 --sends 200 --seed 20261022 --no-anomalies
```

The clean baseline should pass all validation checks. The automated tests also verify a clean 100-cart baseline.

## Automated tests

```bash
pytest -q
```

The tests verify that the clean baseline passes and that the default anomaly run produces exactly the four required ground-truth cases, with exactly the four corresponding validation checks failing.

## Full-size verification

The full-volume run was executed with:

```bash
python main.py --carts 50000 --abandoned 20000 --sends 10000 --seed 20261022
```

Observed output from the verified run:
- 50,000 carts
- 20,000 baseline abandoned carts
- 10,000 send attempts
- 5,000 customers
- 12,287 orders (including non-converting cancelled/refunded records)
- 4 labelled anomalies in `ground_truth.csv`
- 14 validation checks passed; 4 failed exactly as expected for the four injected anomalies

## Reproducibility

The full-size pipeline was run twice with the same seed and configuration. Twenty-five table export files (CSV, JSON and SQL seed dump) were compared. There were zero SHA-256 checksum mismatches and zero row-count mismatches. `source_manifest.json` includes a generation timestamp, so compare the per-file hashes listed inside it rather than comparing the manifest file byte-for-byte.

## Expected anomaly failures

- `cart_total_reconciliation`
- `abandonment_after_purchase`
- `duplicate_order_attribution`
- `message_after_optout`

These failures are intentional and should be matched to the separate ground-truth file. `frequency_cap_compliance`, foreign-key checks and primary-key checks should pass.
