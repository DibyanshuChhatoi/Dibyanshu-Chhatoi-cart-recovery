# YottaFlex AI - E-commerce Cart Recovery Intelligence

A locally executable synthetic data and business-rule pipeline for e-commerce cart abandonment recovery. It generates connected customer, consent, session, cart, campaign, message, order and attribution records; injects labelled edge cases; validates integrity; exports CSV/JSON; and calculates business metrics.

## 1. Requirements

- Python 3.13.5 tested
- Git (for repository submission)
- Windows, macOS or Linux
- Internet is required only to install Python packages; the data pipeline itself runs locally.

## 2. Setup (Windows PowerShell)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run this once for the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Generate a starter dataset

```powershell
python main.py --carts 1000 --abandoned 400 --sends 200 --seed 20261022
```

This creates:
- `data/generated/yottaflex.db`
- CSV files for each entity in `data/generated/`
- `data/generated/source_manifest.json`
- `data/ground_truth/ground_truth.csv`
- `data/reports/validation_report.json`
- `data/reports/analytics_summary.json`

The default run injects four labelled anomaly scenarios after generating baseline records. A pre-generated full-volume artifact is also included at `artifacts/full_dataset.zip`; it contains CSV, JSON and SQL exports, the source manifest, ground truth and validation/analytics reports.

## 4. Validate a clean baseline

```powershell
python main.py --carts 1000 --abandoned 400 --sends 200 --seed 20261022 --no-anomalies
```

This regenerates a clean database without deliberate anomaly injection.

## 5. Generate the requested full dataset

```powershell
python main.py --carts 50000 --abandoned 20000 --sends 10000 --seed 20261022
```

The generator uses the same code path for starter and full volumes.

## 6. Run automated tests

```powershell
pytest -q
```

## 7. Launch the dashboard

After generating data:

```powershell
streamlit run app.py
```

Open the local URL printed by Streamlit.

## 8. Business assumptions

See `docs/business_rules.md`. Key defaults:
- 60-minute inactivity window.
- 7-day attribution window.
- Last eligible recovery click attribution.
- 2-message per-channel frequency cap in a rolling 7-day window.
- Missing consent is treated as denied.

These are documented implementation assumptions, not values explicitly prescribed by the challenge.

## 9. AI-use transparency

See `prompts/prompt-history.md` and `prompts/ai-usage-disclosure.md`. Update the prompt history with every prompt submitted to every AI tool used during development. Do not claim manual review or tests that you have not personally completed.

## 10. Project documentation

- `docs/architecture.md`
- `docs/data_dictionary.md`
- `docs/business_rules.md`
- `docs/testing.md`
- `docs/limitations.md`
- `docs/metrics.md`
- `artifacts/README.md` (description of the full-volume data bundle)

## 11. Important note

All records are synthetic. Email addresses use the reserved `.test` domain. The application does not contact real customers or send real messages.
