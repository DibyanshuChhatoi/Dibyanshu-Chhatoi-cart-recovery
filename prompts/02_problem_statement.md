# Original YottaFlex AI Problem Statement

## Problem statement

Read it carefully. Your build should cover every point below.

Business Context / Problem Identify abandoned carts, respect contact consent and coordinate personalized recovery campaigns with conversion attribution.

Objective and Scope Build a working solution for this end-to-end workflow: Identify abandoned carts, respect contact consent and coordinate personalized recovery campaigns with conversion attribution. The solution should expose key decisions and exceptions, preserve traceability, and produce measurable outputs. Medium complexity means multiple related entities, conditional rules, at least one exception path and meaningful evaluation metrics.

Primary Actors / Systems Customer, store/warehouse operator, merchandising/e-commerce analyst and operations manager.

## Business Workflow and Rules

1. Generate/reference master data first: Customer, Consent, Session, Cart, CartLine.
2. Generate dependent transaction/event records using valid parent IDs.
3. Apply business logic: Generate sessions and carts; create cart updates and inactivity timestamps; define abandonment windows and suppression rules; maintain email/SMS consent and frequency caps; schedule campaign variants; generate send/delivery/open/click events; attribute subsequent orders within a documented window.
4. Persist state changes as explicit records/events where relevant; do not overwrite history.
5. Generate outcomes and ground-truth labels from documented rules, not independent random assignment.

## Entities and Relationships

Core entities: Customer, Consent, Session, Cart, CartLine, Campaign, MessageTemplate, SendAttempt, Order, Attribution. Define a primary key for every entity and foreign keys for every relationship. Document cardinality (1:1, 1:N, N:M), optional relationships, effective dates and lifecycle states. Use bridge tables for many-to-many relationships; retain event history for state changes; validate all joins. For deliberate anomaly cases, keep an issue_type/ground_truth label rather than silently corrupting unrelated rows.

## ID / Nomenclature Conventions

CUS-000001; CART-2026-000001; CMP-2026-000001; MSG-<cart-id>-01; SEND-2026-000001; ORD-2026-000001. Keep counters zero-padded, IDs immutable, and referenced IDs exactly consistent across files.

## Synthetic Data Generation Instructions (Granular)

Step 1 — Write a data dictionary for: Customer, Consent, Session, Cart, CartLine, Campaign, MessageTemplate, SendAttempt, Order, Attribution. For each field specify type, required/optional, allowed values, units, uniqueness and validation rule.

Step 2 — Create parent/master tables first, then child and event tables. Apply this domain-specific generation logic: Generate sessions and carts; create cart updates and inactivity timestamps; define abandonment windows and suppression rules; maintain email/SMS consent and frequency caps; schedule campaign variants; generate send/delivery/open/click events; attribute subsequent orders within a documented window.

Step 3 — Apply deterministic IDs and naming: CUS-000001; CART-2026-000001; CMP-2026-000001; MSG-<cart-id>-01; SEND-2026-000001; ORD-2026-000001. Keep counters zero-padded, IDs immutable, and referenced IDs exactly consistent across files.

Step 4 — Generate the baseline volume: Generate 50,000 carts, 20,000 abandoned carts and 10,000 campaigns/sends. Include consent withdrawal, multiple devices, recovered carts, late purchases and frequency-cap conflicts. Use a fixed seed (e.g. 20261022) and parameterize scale so starter and full datasets use the same generator.

Step 5 — Generate valid baseline records first, then inject labelled edge cases: Message sent after opt-out; cart considered abandoned after purchase; attribution double-counted across campaigns; cart total stale after quantity update.

Step 6 — Calculate derived values (totals, balances, scores, statuses and dates) from source records rather than generating them independently.

Step 7 — Produce a separate ground_truth.csv/json for known anomalies, expected decisions or labels; never leak it into input features.

Step 8 — Run validation: primary-key uniqueness, foreign-key integrity, allowed enums, date ordering, arithmetic reconciliation, lifecycle transitions and duplicate checks.

Step 9 — Export CSV/JSON/SQL seed data plus README, schema/data dictionary, generator command, fixed seed, source manifest and validation summary.

Step 10 — Regenerate twice with the same seed and compare row counts/checksums to demonstrate reproducibility.

## Suggested Volume and Coverage

Generate 50,000 carts, 20,000 abandoned carts and 10,000 campaigns/sends. Include consent withdrawal, multiple devices, recovered carts, late purchases and frequency-cap conflicts.

## Required Edge Cases / Negative Scenarios

- Message sent after opt-out.
- Cart considered abandoned after purchase.
- Attribution double-counted across campaigns.
- Cart total stale after quantity update.

## Validation Rules / Acceptance Criteria

Consent and suppression rules are enforced; abandonment is time-based; attribution is deterministic; conversion metrics reconcile.

## Evaluation Focus for Generated Data Review

(a) realistic distributions and meaningful variation; (b) consistent IDs and valid joins; (c) dependency/lifecycle consistency across entities; (d) correct derived values and reconciliation; (e) normal, boundary, failure and exception coverage; (f) separate ground truth; (g) fixed-seed reproducibility, documentation and lawful provenance.

## Public Data Guidance / Lawful Use

External data is optional. If used, record source URL, dataset/version, retrieval date, license/terms, attribution, transformations and fields discarded. Use only data you are legally permitted to access and redistribute; do not bypass access controls or collect confidential/personal information. If licensing or suitability is unclear, use synthetic data and cite public reference data only for schema inspiration.

## Before you submit, make sure you have

- Pushed your code to a public GitHub repository.
- Added a README explaining how to run it.
- Included any tests the problem asks for.
