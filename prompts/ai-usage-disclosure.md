# AI Usage Disclosure

## Tools used

- ChatGPT: requirement interpretation, architecture discussion, code drafting, documentation drafting, test design and debugging assistance.

## Where AI accelerated the work

- Translated the business statement into a workflow and entity model.
- Proposed a Python/SQLite/Streamlit architecture suitable for local execution.
- Drafted the initial database schema, synthetic data generator, business logic, export routines, validation routines, tests and documentation.
- Assisted with debugging the starter test and performance bottlenecks found during larger-volume validation.

## Candidate review and validation — complete before submission

The candidate must personally:

- Read and understand each core module, especially `generators/synthetic_generator.py`, `engines/business_rules.py`, `validation/anomaly_injector.py`, `validation/validator.py`, `analytics/metrics.py`, and `exports/exporter.py`.
- Run the setup commands and execute the application locally.
- Inspect the SQLite tables, CSV/JSON/SQL exports and ground-truth labels.
- Run `pytest -q` and understand what each test proves.
- Verify the full-volume row counts and repeat-generation checksums.
- Record any code changes personally made and any additional tests run.

Do not submit this disclosure unchanged if any statement above is not true. Update it to accurately describe what was reviewed, changed and personally verified. AI-generated code is not a substitute for candidate understanding or ownership.
