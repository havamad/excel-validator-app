import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="CSV Validator Pro V3", layout="wide")

st.title("📊 CSV Validator Pro — Demo V3")

# -------------------------
# Helpers
# -------------------------

REQUIRED_RULE_COLS = {"column", "rule", "value"}

def load_rules(file):
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip().str.lower()

    if not REQUIRED_RULE_COLS.issubset(df.columns):
        st.error(f"Rules sheet must contain columns: {REQUIRED_RULE_COLS}")
        st.write("Found columns:", list(df.columns))
        st.stop()

    return df


def check_rule(val, rule, rule_value):
    try:
        if rule == "min":
            return float(val) >= float(rule_value)
        elif rule == "max":
            return float(val) <= float(rule_value)
        elif rule == "in":
            allowed = [x.strip() for x in str(rule_value).split(",")]
            return str(val) in allowed
        else:
            return True
    except:
        return False


# -------------------------
# Uploads
# -------------------------

col1, col2 = st.columns(2)

with col1:
    rules_file = st.file_uploader("📘 Upload Rules Excel", type=["xlsx"])

with col2:
    data_file = st.file_uploader("📄 Upload Data CSV", type=["csv"])


if rules_file and data_file:

    rules_df = load_rules(rules_file)
    data_df = pd.read_csv(data_file)

    st.subheader("🔍 Rules Preview")
    st.dataframe(rules_df)

    # -------------------------
    # Validation
    # -------------------------

    fail_records = []
    column_score = {}
    total_checks = 0
    total_pass = 0

    for _, r in rules_df.iterrows():
        col = r["column"]
        rule = r["rule"]
        value = r["value"]

        if col not in data_df.columns:
            st.warning(f"Column missing in data: {col}")
            continue

        passed_mask = data_df[col].apply(lambda x: check_rule(x, rule, value))

        total_checks += len(passed_mask)
        total_pass += passed_mask.sum()

        column_score[col] = f"{passed_mask.sum()}/{len(passed_mask)}"

        failed_rows = data_df[~passed_mask].copy()
        if not failed_rows.empty:
            failed_rows["failed_column"] = col
            failed_rows["failed_rule"] = rule
            fail_records.append(failed_rows)

    # -------------------------
    # Results
    # -------------------------

    st.divider()
    st.header("📈 Validation Summary")

    pass_pct = round((total_pass / total_checks) * 100, 2) if total_checks else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Checks", total_checks)
    m2.metric("Passed", total_pass)
    m3.metric("Pass %", f"{pass_pct}%")

    # -------------------------
    # Column Score
    # -------------------------

    st.subheader("✅ Column Wise Score")
    st.json(column_score)

    # -------------------------
    # Failed Rows
    # -------------------------

    if fail_records:
        failed_df = pd.concat(fail_records)

        st.error(f"❌ Failed Rows: {len(failed_df)}")
        st.dataframe(failed_df)

        csv_bytes = failed_df.to_csv(index=False).encode()
        st.download_button(
            "⬇️ Download Failed Rows CSV",
            csv_bytes,
            "failed_rows.csv",
            "text/csv"
        )

    else:
        st.success("🎉 All rows passed validation")

    # -------------------------
    # Excel Report
    # -------------------------

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        data_df.to_excel(writer, sheet_name="All Data", index=False)
        if fail_records:
            failed_df.to_excel(writer, sheet_name="Failed Rows", index=False)
        rules_df.to_excel(writer, sheet_name="Rules", index=False)

    st.download_button(
        "📥 Download Full Excel Report",
        output.getvalue(),
        "validation_report.xlsx"
    )

else:
    st.info("Upload Rules Excel + Data CSV to start validation.")
