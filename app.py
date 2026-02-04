import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="CSV Validator Pro V2", layout="wide")

st.title("📊 CSV Validator Pro V2")

# -----------------------------
# RULE LOADER (AUTO FIX HEADERS)
# -----------------------------
REQUIRED_RULE_COLS = ["column", "rule", "value"]

def load_rules(file):
    df = pd.read_excel(file)

    # normalize headers
    df.columns = df.columns.str.strip().str.lower()

    # allow "type" instead of "rule"
    if "type" in df.columns and "rule" not in df.columns:
        df = df.rename(columns={"type": "rule"})

    for c in REQUIRED_RULE_COLS:
        if c not in df.columns:
            st.error(f"Missing column in rules sheet: {c}")
            st.write("Found columns:", list(df.columns))
            st.stop()

    return df


# -----------------------------
# RULE CHECKER
# -----------------------------
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


# -----------------------------
# FILE UPLOAD
# -----------------------------
rules_file = st.file_uploader("Upload Rules Excel", type=["xlsx"])
data_file = st.file_uploader("Upload Data CSV", type=["csv"])

if rules_file and data_file:

    rules_df = load_rules(rules_file)
    data_df = pd.read_csv(data_file)

    st.subheader("🔍 Rules Preview")
    st.dataframe(rules_df)

    failed_rows = []
    column_scores = {}

    # -----------------------------
    # VALIDATION LOOP
    # -----------------------------
    for _, r in rules_df.iterrows():
        col = r["column"]
        rule = str(r["rule"]).lower()
        value = r["value"]

        if col not in data_df.columns:
            st.warning(f"Column not found in data: {col}")
            continue

        results = data_df[col].apply(lambda x: check_rule(x, rule, value))

        pass_count = results.sum()
        total = len(results)

        column_scores[col] = f"{pass_count}/{total}"

        bad = data_df[~results]
        if not bad.empty:
            bad["__failed_column"] = col
            bad["__failed_rule"] = rule
            failed_rows.append(bad)

    # -----------------------------
    # SUMMARY
    # -----------------------------
    st.subheader("✅ Column Wise Score")
    st.write(column_scores)

    if failed_rows:
        failed_df = pd.concat(failed_rows)

        st.subheader("❌ Failed Rows")
        st.dataframe(failed_df)

        # download failed rows
        csv_bytes = failed_df.to_csv(index=False).encode()

        st.download_button(
            "⬇️ Download Failed Rows CSV",
            csv_bytes,
            file_name="failed_rows.csv"
        )

        st.error(f"Total Failed Rows: {len(failed_df)}")

    else:
        st.success("🎉 All rows passed validation!")

    # -----------------------------
    # EXCEL REPORT EXPORT
    # -----------------------------
    output = BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        data_df.to_excel(writer, sheet_name="data", index=False)
        rules_df.to_excel(writer, sheet_name="rules", index=False)

        if failed_rows:
            failed_df.to_excel(writer, sheet_name="failed", index=False)

    st.download_button(
        "📥 Download Full Excel Report",
        output.getvalue(),
        file_name="validation_report.xlsx"
    )
