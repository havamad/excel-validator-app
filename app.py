import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="CSV Validator Pro", layout="wide")

st.title("📊 CSV Validator Pro v2")

# -----------------------------
# Helpers
# -----------------------------

REQUIRED_RULE_COLS = {"column", "rule", "value"}

def load_rules(file):
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip().str.lower()
    if not REQUIRED_RULE_COLS.issubset(df.columns):
        st.error(f"Rules sheet must contain columns: {REQUIRED_RULE_COLS}")
        st.stop()
    return df

def check_rule(val, rule, rule_value):
    try:
        if rule == "min":
            return float(val) >= float(rule_value)
        if rule == "max":
            return float(val) <= float(rule_value)
        if rule == "in":
            allowed = [x.strip() for x in str(rule_value).split(",")]
            return str(val) in allowed
    except:
        return False
    return True

def validate(df, rules_df):
    results = []
    error_cols = []
    error_msgs = []

    for _, row in df.iterrows():
        row_errors = []
        row_cols = []

        for _, r in rules_df.iterrows():
            col = r["column"]
            rule = str(r["rule"]).lower()
            rule_val = r["value"]

            if col not in df.columns:
                continue

            ok = check_rule(row[col], rule, rule_val)
            if not ok:
                row_errors.append(f"{col}:{rule}")
                row_cols.append(col)

        results.append(len(row_errors) == 0)
        error_cols.append(",".join(row_cols))
        error_msgs.append(",".join(row_errors))

    df_out = df.copy()
    df_out["status"] = ["PASS" if x else "FAIL" for x in results]
    df_out["error_columns"] = error_cols
    df_out["error_rules"] = error_msgs

    return df_out

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="report")
    return output.getvalue()

# -----------------------------
# Upload UI
# -----------------------------

rules_file = st.file_uploader("Upload Rules Excel", type=["xlsx"])
data_file = st.file_uploader("Upload Data CSV", type=["csv"])

if rules_file and data_file:

    rules_df = load_rules(rules_file)
    data_df = pd.read_csv(data_file)

    st.subheader("🔍 Rules Preview")
    st.dataframe(rules_df)

    # -------------------------
    # Validation
    # -------------------------

    validated = validate(data_df, rules_df)

    passed = (validated["status"] == "PASS").sum()
    failed = (validated["status"] == "FAIL").sum()
    total = len(validated)

    # -------------------------
    # Summary
    # -------------------------

    st.subheader("✅ Validation Summary")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Rows", total)
    c2.metric("Passed", passed)
    c3.metric("Failed", failed)
    c4.metric("Pass %", round(passed/total*100, 1))

    # -------------------------
    # Column Wise Score
    # -------------------------

    st.subheader("📈 Column Wise Score")

    col_scores = []
    for col in rules_df["column"].unique():
        if col in validated.columns:
            fails = validated[validated["error_columns"].str.contains(col, na=False)]
            score = 100 - (len(fails)/total*100)
            col_scores.append((col, round(score,1)))

    score_df = pd.DataFrame(col_scores, columns=["column","pass_%"])
    st.dataframe(score_df)

    # -------------------------
    # Failed Rows Download
    # -------------------------

    failed_df = validated[validated["status"] == "FAIL"]

    if len(failed_df) > 0:
        st.subheader("❌ Failed Rows")
        st.dataframe(failed_df)

        st.download_button(
            "⬇️ Download Failed Rows Excel",
            to_excel(failed_df),
            file_name="failed_rows.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # -------------------------
    # Full Report Download
    # -------------------------

    st.subheader("📦 Full Validation Report")

    st.download_button(
        "⬇️ Download Full Excel Report",
        to_excel(validated),
        file_name="validation_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.subheader("📋 Full Result Preview")
    st.dataframe(validated)

else:
    st.info("Upload rules + CSV to start validation.")
