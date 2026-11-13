"""Export database tables to CSV and a source manifest."""
import csv
import hashlib
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

TABLES = ["customers","consents","sessions","carts","cart_lines","cart_update_events",
          "campaigns","message_templates","send_attempts","message_events","orders","attributions"]

def export_all(db_path: str, output_dir: str, seed: int):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    manifest = {"seed": seed, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "database": db_path, "files": {}}
    for table in TABLES:
        rows = conn.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
        cols = [d[0] for d in conn.execute(f"SELECT * FROM {table} LIMIT 0").description]
        path = out / f"{table}.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            writer.writerows(rows)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest["files"][path.name] = {"rows": len(rows), "sha256": digest}
        json_path = out / f"{table}.json"
        json_rows = [dict(zip(cols, row)) for row in rows]
        json_path.write_text(json.dumps(json_rows, indent=2, ensure_ascii=False), encoding="utf-8")
        manifest["files"][json_path.name] = {
            "rows": len(json_rows), "sha256": hashlib.sha256(json_path.read_bytes()).hexdigest()
        }
    # SQL seed file can recreate the exported database contents locally.
    sql_path = out / "seed_data.sql"
    sql_path.write_text("\n".join(conn.iterdump()), encoding="utf-8")
    manifest["files"][sql_path.name] = {
        "rows": None, "sha256": hashlib.sha256(sql_path.read_bytes()).hexdigest()
    }
    conn.close()
    (out / "source_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
