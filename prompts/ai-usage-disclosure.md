
# AI Usage Disclosure

## AI tools used

- ChatGPT: requirement analysis, architecture planning, code generation, documentation drafting, test design, debugging and validation guidance.

## AI-assisted work

ChatGPT assisted with:
- Translating the business requirements into a data workflow and entity model.
- Designing the Python, SQLite and Streamlit project structure.
- Drafting the database schema and synthetic data generator.
- Drafting business rules, anomaly injection, validation, analytics and export modules.
- Drafting automated tests, README and technical documentation.
- Troubleshooting environment setup, execution and validation.

## Candidate execution and verification

The candidate personally performed the following project execution and verification steps:

- Created and activated a Python virtual environment using Python 3.13.5.
- Installed the project dependencies.
- Executed the automated test suite; both available tests passed.
- Generated the full dataset using 50,000 carts, 20,000 baseline abandoned carts and 10,000 send attempts.
- Ran the Streamlit dashboard locally and inspected its displayed metrics, charts, campaign results, suppression decisions and validation results.
- Inspected the generated ground-truth anomaly records and validation report.
- Repeated full dataset generation with seed 20261022.
- Compared SHA-256 checksums of CSV, JSON and SQL exports, excluding the timestamp-dependent source manifest. No differences were found.

## Candidate review still required

Before submission, the candidate must personally:

- Read and understand the core source modules and be able to explain their logic.
- Understand the database relationships, business rules, validation checks and analytics calculations.
- Review the generated exports and documentation.
- Be able to explain the assumptions, limitations and design trade-offs.
- Record any additional changes and tests performed.

## Transparency statement

AI assistance was used extensively, including for drafting implementation code. The candidate executed the project locally and performed the verification steps listed above. AI-generated code should not be represented as independently written by the candidate. The candidate is responsible for reviewing, understanding and explaining the submitted work.
