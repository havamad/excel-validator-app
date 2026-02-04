import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="CSV Validator Pro V3", layout="wide")

st.title("CSV Validator Pro V3")

# ---------- RULE LOADER (FIXED) ----------

def load_rules(file):
    df = pd.read_excel(file)

    # normalize headers
    df.columns = df.columns.str.strip().str.lower()

    # support both rule/type column names
    if "type" in df.columns and "rule" not in df.columns:
        df = df.rename(columns={"type": "rule"})

    needed = ["column", "rule", "value"]

    for c in needed:
        if c not in df.columns:
            st.error(f"Missing column in rules sheet: {c}")
            st.write("Found columns:", list(df.columns))
            st.stop()

    return df


# ---------- RULE CHECK ----------

def check_rule(val, rule, rule_value):
    try:
        if rule == "min":
            return float(val) >= float(rule_value)

        if rule == "max":
            return float(val) <= float(rule_value)

        if rule == "in":
            allowed = [x.strip() for x in str(rule_value).split(",")]
            return str(val) in allowed

        return True
    except:
        return False


# ---------- UPLOAD ----------

col1, col2 = st.columns(2)

with col1:
    data_file = st.file_uploader("Upload Data CSV", type=["csv"])

with col2:
    rules_file = st.file_uploader("Upload Rules Excel", type=["xlsx"])


if data_file and rules_file:

    data = pd.read_csv(data_file)
    rules = load_rules(rules_file)

    st.subheader("Rules Preview")
    st.dataframe(rules)

    failed_rows = []
    column_score = {}

    for _, r in rules.iterrows():
        col = r["column"]
        rule = str(r["rule"]).lower()
        val = r["value"]

        if col not in data.columns:
            st.warning(f"Column not found in data: {col}")
            continue

        mask = data[col].apply(lambda x: check_rule(x, rule, val))

        passed = mask.sum()
        total = len(mask)

        column_score[col] = f"{passed}/{total}"

        fail_part = data[~mask].copy()
        fail_part["failed_column"] = col
        fail_part["failed_rule"] = rule

        failed_rows.append(fail_part)

    # ---------- SUMMARY ----------

    st.subheader("Column Wise Score")
    st.json(column_score)

    if failed_rows:
        failed_df = pd.concat(failed_rows)

        st.subheader("Failed Rows")
        st.dataframe(failed_df)

        st.write("Total Failed Rows:", len(failed_df))

        # download csv
        csv = failed_df.to_csv(index=False).encode()
        st.download_button(
            "Download Failed Rows CSV",
            csv,
            "failed_rows.csv",
            "text/csv"
        )

        # excel report
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            data.to_excel(writer, sheet_name="data", index=False)
            failed_df.to_excel(writer, sheet_name="failed", index=False)

        st.download_button(
            "Download Full Excel Report",
            buffer.getvalue(),
            "report.xlsx"
        )

    else:
        st.success("All rows passed ✅")
