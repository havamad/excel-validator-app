import streamlit as st
import pandas as pd

st.set_page_config(page_title="CSV Data Validator Pro", layout="wide")

st.title("📊 CSV Data Validator Pro")

rules_file = st.file_uploader("Upload Rules Excel", type=["xlsx"])
data_file = st.file_uploader("Upload Data CSV", type=["csv"])

def normalize_cols(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
    )
    return df

if rules_file and data_file:

    try:
        # ---------- LOAD RULES ----------
        rules_df = pd.read_excel(rules_file)

        rules_df = normalize_cols(rules_df)

        st.subheader("🔍 Rules Preview")
        st.dataframe(rules_df)

        required = {"column","value","rule"}

        if not required.issubset(set(rules_df.columns)):
            st.error(f"Rules sheet must contain columns: {required}")
            st.stop()

        # ---------- LOAD DATA ----------
        data_df = pd.read_csv(data_file)
        data_df = normalize_cols(data_df)

        st.subheader("📄 Data Preview")
        st.dataframe(data_df.head())

        errors = []

        # ---------- APPLY RULES ----------
        for _, r in rules_df.iterrows():
            col = r["column"]
            rule = str(r["rule"]).lower()
            val = r["value"]

            if col not in data_df.columns:
                errors.append(f"Missing column in data: {col}")
                continue

            if rule == "min":
                bad = data_df[data_df[col] < float(val)]
                if not bad.empty:
                    errors.append(f"{col} below min {val}")

            elif rule == "max":
                bad = data_df[data_df[col] > float(val)]
                if not bad.empty:
                    errors.append(f"{col} above max {val}")

            elif rule == "allowed":
                allowed_vals = [x.strip().lower() for x in str(val).split(",")]
                bad = data_df[~data_df[col].astype(str).str.lower().isin(allowed_vals)]
                if not bad.empty:
                    errors.append(f"{col} has invalid values")

        # ---------- RESULTS ----------
        if errors:
            st.error("❌ Validation Errors Found")
            for e in errors:
                st.write("•", e)
        else:
            st.success("✅ All rules passed!")

    except Exception as e:
        st.exception(e)

else:
    st.info("Upload Rules Excel and Data CSV to start validation.")
