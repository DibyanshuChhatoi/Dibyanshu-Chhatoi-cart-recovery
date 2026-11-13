"""CLI entry point: generate -> inject labelled anomalies -> validate -> export -> metrics."""
import argparse
import json
from pathlib import Path

from config import Settings
from generators.synthetic_generator import generate
from validation.anomaly_injector import inject
from validation.validator import validate
from exports.exporter import export_all
from analytics.metrics import calculate

def main():
    parser = argparse.ArgumentParser(description="YottaFlex synthetic cart recovery pipeline")
    parser.add_argument("--carts", type=int, default=None)
    parser.add_argument("--abandoned", type=int, default=None)
    parser.add_argument("--sends", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--no-anomalies", action="store_true")
    args = parser.parse_args()

    base = Settings.from_env()
    settings = Settings(
        seed=args.seed if args.seed is not None else base.seed,
        carts=args.carts if args.carts is not None else base.carts,
        abandoned_carts=args.abandoned if args.abandoned is not None else base.abandoned_carts,
        send_attempts=args.sends if args.sends is not None else base.send_attempts,
        inactivity_minutes=base.inactivity_minutes,
        attribution_days=base.attribution_days,
        email_cap=base.email_cap, sms_cap=base.sms_cap, cap_window_days=base.cap_window_days,
        simulation_start=base.simulation_start, db_path=base.db_path,
        output_dir=base.output_dir, ground_truth_dir=base.ground_truth_dir,
        reports_dir=base.reports_dir
    )
    settings.validate()
    print("[1/5] Generating valid baseline data...")
    summary = generate(settings)
    ground_truth_path = Path(settings.ground_truth_dir) / "ground_truth.csv"
    if not args.no_anomalies:
        print("[2/5] Injecting labelled edge cases...")
        inject(settings.db_path, str(ground_truth_path))
    else:
        print("[2/5] Skipping anomaly injection.")
        if ground_truth_path.exists():
            ground_truth_path.unlink()  # do not leave stale labels from a previous anomaly run
    print("[3/5] Running validation...")
    report = validate(settings.db_path, str(Path(settings.reports_dir) / "validation_report.json"))
    print("[4/5] Exporting CSV files and manifest...")
    manifest = export_all(settings.db_path, settings.output_dir, settings.seed)
    print("[5/5] Calculating analytics...")
    metrics = calculate(settings.db_path)
    Path(settings.reports_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.reports_dir, "analytics_summary.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print("\nGeneration summary:")
    print(json.dumps(summary, indent=2))
    print("\nAnalytics:")
    print(json.dumps(metrics, indent=2))
    print(f"\nValidation: {report['summary']['passed']} passed / {report['summary']['failed']} failed")
    print("Note: when anomalies are injected, selected validation checks are expected to fail.")
    print(f"Database: {settings.db_path}")
    print(f"CSV exports: {settings.output_dir}")
    print(f"Ground truth: {settings.ground_truth_dir}/ground_truth.csv")

if __name__ == "__main__":
    main()
