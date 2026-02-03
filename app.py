import streamlit as st
import pandas as pd

st.title("CSV Data Validator Pro")

# ---------- RULE LOADER ----------
def load_rules(excel_file):
    df = pd.read_excel(excel_file)

    # normalize column names
    df.columns = df.columns.str.strip().str.lower()

    # allow rule or type
    if "rule" not in df.columns and "type" in df.columns:
        df = df.rename(columns={"type": "rule"})

    required = {"column", "rule", "value"}

    if not required.issubset(set(df.columns)):
        st.error(f"Rules sheet must contain columns: {required}")
        st.stop()

    return df


# ---------- VALIDATOR ----------
def validate(df, rules_df):
    errors = []

    for _, r in rules_df.iterrows():
        col = r["column"]
        rule = str(r["rule"]).lower()
        val = r["value"]

        if col not in df.columns:
            errors.append(f"Missing column: {col}")
            continue

        if rule == "min":
            bad = df[df[col] < float(val)]
            errors.append((col, "min", bad))

        elif rule == "max":
            bad = df[df[col] > float(val)]
            errors.append((col, "max", bad))

        elif rule == "in":
            allowed = [x.strip() for x in str(val).split(",")]
            bad = df[~df[col].astype(str).isin(allowed)]
            errors.append((col, "in", bad))

    return errors


# ---------- UI ----------
rules_file = st.file_uploader("Upload Rules Excel", type=["xlsx"])
data_file = st.file_uploader("Upload Data CSV", type=["csv"])

if rules_file and data_file:

    rules_df = load_rules(rules_file)
    data_df = pd.read_csv(data_file)

    st.subheader("Rules Preview")
    st.dataframe(rules_df)

    errs = validate(data_df, rules_df)

    st.subheader("Validation Results")

    for e in errs:
        if isinstance(e, tuple):
            col, rule, bad = e
            if len(bad) > 0:
                st.error(f"{col} failed {rule} rule — {len(bad)} rows")
                st.dataframe(bad.head())
            else:
                st.success(f"{col} passed {rule}")
