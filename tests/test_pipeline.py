from pathlib import Path
import json

from config import Settings
from generators.synthetic_generator import generate
from validation.anomaly_injector import inject
from validation.validator import validate
from analytics.metrics import calculate


def test_small_pipeline_injects_and_detects_all_four_required_anomalies(tmp_path):
    db = str(tmp_path / "test.db")
    settings = Settings(carts=100, abandoned_carts=40, send_attempts=20, db_path=db)
    result = generate(settings)
    assert result["carts"] == 100
    gt = str(tmp_path / "ground_truth.csv")
    anomalies = inject(db, gt)
    assert len(anomalies) == 4
    report = validate(db, str(tmp_path / "report.json"))
    assert report["row_counts"]["carts"] == 100
    assert Path(gt).exists()
    failed = {c["check"] for c in report["checks"] if not c["passed"]}
    assert failed == {
        "cart_total_reconciliation",
        "abandonment_after_purchase",
        "duplicate_order_attribution",
        "message_after_optout",
    }
    metrics = calculate(db)
    assert metrics["carts"] == 100
    assert metrics["abandoned_carts"] >= 40  # includes the deliberately injected post-purchase anomaly
    assert metrics["attributed_orders"] >= 1


def test_clean_baseline_passes_all_validation_checks(tmp_path):
    db = str(tmp_path / "clean.db")
    settings = Settings(carts=100, abandoned_carts=40, send_attempts=20, db_path=db)
    result = generate(settings)
    report = validate(db, str(tmp_path / "clean-report.json"))
    assert result["carts"] == 100
    assert report["summary"]["failed"] == 0
    assert report["summary"]["passed"] == report["summary"]["checks"]
