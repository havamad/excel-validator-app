import streamlit as st
import pandas as pd
from io import BytesIO

st.title("CSV Data Validator")

# ---------- RULES LOADER ----------
def load_rules(rule_file):
    xls = pd.ExcelFile(rule_file)
    rules_df = pd.read_excel(xls, "rules")
    return rules_df

# ---------- VALIDATOR ----------
def validate(df, rules_df):
    errors = []

    for _, rule in rules_df.iterrows():
        col = rule["column"]
        rtype = rule["type"]

        if col not in df.columns:
            continue

        if rtype == "min":
            minv = rule["value"]
            bad = df[df[col] < minv]
            for i in bad.index:
                errors.append({"row": i, "column": col, "error": "below min"})

        elif rtype == "max":
            maxv = rule["value"]
            bad = df[df[col] > maxv]
            for i in bad.index:
                errors.append({"row": i, "column": col, "error": "above max"})

        elif rtype == "in":
            allowed = str(rule["value"]).split("|")
            bad = df[~df[col].astype(str).isin(allowed)]
            for i in bad.index:
                errors.append({"row": i, "column": col, "error": "invalid"})

    return pd.DataFrame(errors)

# ---------- UI ----------
rule_file = st.file_uploader("Upload Rules Excel", type=["xlsx"])
data_file = st.file_uploader("Upload Data CSV", type=["csv"])

if rule_file and data_file:

    rules_df = load_rules(rule_file)
    df = pd.read_csv(data_file)

    st.success("Files loaded")

    err_df = validate(df, rules_df)

    st.subheader("Validation Errors")
    st.dataframe(err_df)

    # ---------- CLEAN DATA ----------
    bad_rows = err_df["row"].unique() if not err_df.empty else []
    clean_df = df.drop(index=bad_rows)

    # ---------- DOWNLOAD CSV ----------
    st.download_button(
        "Download Errors CSV",
        err_df.to_csv(index=False),
        file_name="errors.csv"
    )

    # ---------- EXCEL REPORT ----------
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Original")
        clean_df.to_excel(writer, index=False, sheet_name="Clean")
        err_df.to_excel(writer, index=False, sheet_name="Errors")

    st.download_button(
        "Download Full Excel Report",
        output.getvalue(),
        file_name="report.xlsx"
    )