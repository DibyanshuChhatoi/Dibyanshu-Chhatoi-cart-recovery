"""Optional Streamlit dashboard for generated pipeline outputs."""
import json
from pathlib import Path
import subprocess
import sys
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="YottaFlex Cart Recovery", page_icon="🛒", layout="wide")
st.title("E-commerce Cart Recovery Intelligence")
st.caption("Synthetic data generation, recovery decisions, attribution and data-quality validation")

with st.sidebar:
    st.header("Generate dataset")
    carts_input = st.number_input("Carts", min_value=100, max_value=50000, value=1000, step=100)
    abandoned_input = st.number_input("Abandoned carts", min_value=0, max_value=int(carts_input), value=min(400, int(carts_input)), step=100)
    sends_input = st.number_input("Send attempts", min_value=0, max_value=int(abandoned_input), value=min(200, int(abandoned_input)), step=50)
    seed_input = st.number_input("Fixed seed", min_value=1, value=20261022, step=1)
    inject_input = st.checkbox("Inject four labelled anomalies", value=True)
    if st.button("Generate and validate", type="primary"):
        command = [sys.executable, "main.py", "--carts", str(int(carts_input)),
                   "--abandoned", str(int(abandoned_input)), "--sends", str(int(sends_input)),
                   "--seed", str(int(seed_input))]
        if not inject_input:
            command.append("--no-anomalies")
        with st.spinner("Generating records and running validation..."):
            result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            st.success("Pipeline completed. Dashboard data refreshed.")
            st.code(result.stdout[-5000:])
            st.rerun()
        else:
            st.error("Pipeline failed")
            st.code(result.stderr or result.stdout)

metrics_path = Path("data/reports/analytics_summary.json")
validation_path = Path("data/reports/validation_report.json")
db_path = Path("data/generated/yottaflex.db")

if not metrics_path.exists():
    st.info("No generated dataset found. Run `python main.py --carts 1000 --abandoned 400 --sends 200` first.")
    st.stop()

m = json.loads(metrics_path.read_text(encoding="utf-8"))
cols = st.columns(4)
for col, label, key in zip(cols, ["Carts","Abandoned carts","Send attempts","Attributed revenue"],
                           ["carts","abandoned_carts","send_attempts","attributed_revenue"]):
    col.metric(label, f"₹{m[key]:,.0f}" if key == "attributed_revenue" else f"{m[key]:,}")

st.subheader("Recovery performance")
a, b, c, d = st.columns(4)
a.metric("Abandonment rate", f"{m['abandonment_rate_pct']}%")
b.metric("Recovery rate", f"{m['recovery_rate_pct']}%")
c.metric("Delivery rate", f"{m['delivery_rate_pct']}%")
d.metric("Click rate", f"{m['click_rate_pct']}%")
e, f = st.columns(2)
e.metric("Attributed conversion rate", f"{m['conversion_rate_pct']}%")
f.metric("Suppressed attempts", f"{m['suppressed_attempts']:,}")

if db_path.exists():
    carts = pd.read_csv("data/generated/carts.csv")
    status_counts = carts["status"].value_counts().rename_axis("status").reset_index(name="count")
    st.plotly_chart(px.bar(status_counts, x="status", y="count", title="Cart lifecycle status"), use_container_width=True)
    campaigns = pd.read_sql_query("""SELECT c.campaign_id,c.campaign_name,c.channel,
        COUNT(s.send_id) AS attempts,
        SUM(CASE WHEN s.sent_at IS NOT NULL THEN 1 ELSE 0 END) AS sent,
        SUM(CASE WHEN s.status='SUPPRESSED' THEN 1 ELSE 0 END) AS suppressed
        FROM campaigns c LEFT JOIN send_attempts s ON s.campaign_id=c.campaign_id
        GROUP BY c.campaign_id,c.campaign_name,c.channel ORDER BY c.campaign_id""",
        __import__("sqlite3").connect(str(db_path)))
    st.subheader("Campaign performance")
    st.dataframe(campaigns, use_container_width=True, hide_index=True)

st.subheader("Data-quality validation")
if validation_path.exists():
    report = json.loads(validation_path.read_text(encoding="utf-8"))
    st.write(f"Checks passed: **{report['summary']['passed']}** · Checks failed: **{report['summary']['failed']}**")
    st.dataframe(pd.DataFrame(report["checks"]), use_container_width=True, hide_index=True)
else:
    st.warning("Validation report not found.")

truth_path = Path("data/ground_truth/ground_truth.csv")
if truth_path.exists():
    st.subheader("Injected ground-truth anomalies")
    st.dataframe(pd.read_csv(truth_path), use_container_width=True, hide_index=True)

st.subheader("Suppression decisions")
if Path("data/generated/send_attempts.csv").exists():
    sends = pd.read_csv("data/generated/send_attempts.csv")
    suppressed = sends[sends["status"] == "SUPPRESSED"]
    st.dataframe(suppressed[["send_id","customer_id","channel","suppression_reason"]].head(100),
                 use_container_width=True, hide_index=True)
