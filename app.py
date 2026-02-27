import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from model import GuardianAuditor

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="GuardianSQL | Data Quality Auditor",
    layout="wide"
)

# -------------------------------------------------
# PROFESSIONAL STYLING
# -------------------------------------------------
st.markdown("""
<style>
.main {
    background-color: #f7f9fb;
}
h1, h2, h3 {
    font-weight: 600;
}
[data-testid="metric-container"] {
    background-color: white;
    border: 1px solid #e6e9ef;
    padding: 18px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("GuardianSQL")
st.caption("Enterprise Data Quality & Governance Auditor")

st.markdown("---")

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "use_sample_data" not in st.session_state:
    st.session_state.use_sample_data = False

if "cleaned_df" not in st.session_state:
    st.session_state.cleaned_df = None

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.header("Data Configuration")

if st.sidebar.button("Load Enterprise Sample Dataset"):
    st.session_state.use_sample_data = True
    st.session_state.cleaned_df = None

st.sidebar.markdown("OR")

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    st.session_state.use_sample_data = False
    st.session_state.cleaned_df = None

# -------------------------------------------------
# DATA LOADING
# -------------------------------------------------
df = None

try:
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if df.empty:
            st.error("Uploaded file is empty.")
            st.stop()

    elif st.session_state.use_sample_data:

        np.random.seed(42)
        n = 1500

        df = pd.DataFrame({
            "Transaction_ID": np.arange(10000, 10000 + n),
            "Customer_ID": np.random.randint(1000, 5000, n),
            "Region": np.random.choice(["North", "South", "East", "West"], n),
            "Category": np.random.choice(
                ["Electronics", "Furniture", "Clothing", "Sports"], n
            ),
            "Revenue": np.random.normal(8000, 2500, n).round(2),
            "Cost": np.random.normal(5500, 1800, n).round(2),
            "Discount": np.random.uniform(0, 0.35, n).round(2),
            "Order_Date": pd.date_range("2023-01-01", periods=n, freq="D")
        })

        # Inject quality issues
        df.loc[np.random.choice(n, 60), "Revenue"] = -200
        df.loc[np.random.choice(n, 50), "Cost"] = np.nan
        df.loc[np.random.choice(n, 30), "Category"] = None
        df = pd.concat([df, df.iloc[:12]])

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# -------------------------------------------------
# MAIN LOGIC
# -------------------------------------------------
if df is not None:

    auditor = GuardianAuditor(df)

    # Sidebar settings
    st.sidebar.markdown("---")
    st.sidebar.subheader("Audit Settings")

    numeric_cols_available = df.select_dtypes(include=["number"]).columns.tolist()

    numeric_cols = st.sidebar.multiselect(
        "Numeric Columns",
        numeric_cols_available,
        default=[col for col in ["Revenue", "Cost"] if col in numeric_cols_available]
    )

    date_col = st.sidebar.selectbox(
        "Date Column",
        ["None"] + df.columns.tolist()
    )

    col_list = df.columns.tolist()

    st.sidebar.markdown("---")
    st.sidebar.subheader("Consistency Rule")
    st.sidebar.caption("Column A must be greater than or equal to Column B")

    col_a = st.sidebar.selectbox("Column A", col_list, index=0)
    col_b = st.sidebar.selectbox("Column B", col_list, index=1 if len(col_list) > 1 else 0)

    # Run checks
    completeness_dict = auditor.check_completeness()
    dupe_count = auditor.check_uniqueness()

    validity_results = auditor.check_validity(numeric_cols) if numeric_cols else {}
    outlier_results = auditor.check_accuracy(numeric_cols) if numeric_cols else {}

    if date_col != "None":
        auditor.check_timeliness(date_col)

    inc_count = auditor.check_consistency(col_a, col_b)
    overall_score = auditor.get_overall_health_score()

    # -------------------------------------------------
    # TOP METRICS
    # -------------------------------------------------
    total_missing = sum(completeness_dict.values())
    total_cells = df.shape[0] * df.shape[1]
    missing_pct = round((total_missing / total_cells) * 100, 2)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Overall Data Health", f"{overall_score:.1f}%")
    m2.metric("Total Records", f"{len(df):,}")
    m3.metric("Duplicate Rows", f"{dupe_count:,}")
    m4.metric("Missing Values", f"{total_missing:,} ({missing_pct}%)")

    st.markdown("---")

    # -------------------------------------------------
    # TABS
    # -------------------------------------------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Profiling",
        "Validity",
        "Accuracy",
        "Dataset",
        "Remediation"
    ])

    # -------------------------------------------------
    # TAB 1 — PROFILING
    # -------------------------------------------------
    with tab1:

        st.subheader("Missing Values by Column")

        if completeness_dict:
            null_df = pd.DataFrame(
                list(completeness_dict.items()),
                columns=["Column", "Missing Count"]
            )

            null_df["Missing %"] = (
                null_df["Missing Count"] / len(df) * 100
            ).round(2)

            null_df = null_df.sort_values("Missing %", ascending=False)

            fig = px.bar(
                null_df,
                x="Column",
                y="Missing %",
                text="Missing %",
                color="Missing %",
                color_continuous_scale="Blues",
                template="plotly_white"
            )

            fig.update_traces(texttemplate='%{text}%', textposition='outside')
            fig.update_layout(
                height=500,
                yaxis_title="Missing Percentage (%)",
                xaxis_title="Columns",
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Schema Overview")

        schema_df = pd.DataFrame({
            "Data Type": df.dtypes.astype(str),
            "Unique Values": df.nunique(),
            "Memory Usage (KB)": (df.memory_usage(deep=True) / 1024).round(2)
        })

        st.dataframe(schema_df, use_container_width=True)

    # -------------------------------------------------
    # TAB 2 — VALIDITY
    # -------------------------------------------------
    with tab2:

        colL, colR = st.columns(2)

        with colL:
            st.subheader("Duplicate Check")
            if dupe_count > 0:
                st.error(f"{dupe_count:,} duplicate rows detected.")
            else:
                st.success("No duplicate rows detected.")

        with colR:
            st.subheader("Negative Value Check")
            if numeric_cols:
                st.json(validity_results)
            else:
                st.info("Select numeric columns in the sidebar.")

    # -------------------------------------------------
    # TAB 3 — ACCURACY
    # -------------------------------------------------
    with tab3:

        st.subheader("Outlier Distribution")

        if numeric_cols:
            fig_box = px.box(
                df,
                y=numeric_cols,
                points="outliers",
                template="plotly_white"
            )

            fig_box.update_layout(height=500)
            st.plotly_chart(fig_box, use_container_width=True)
            st.json(outlier_results)
        else:
            st.info("Select numeric columns.")

    # -------------------------------------------------
    # TAB 4 — DATA VIEW
    # -------------------------------------------------
    with tab4:
        st.dataframe(df, use_container_width=True)

    # -------------------------------------------------
    # TAB 5 — REMEDIATION
    # -------------------------------------------------
    with tab5:

        st.subheader("Apply Cleaning Rules")

        drop_dupes = st.checkbox("Remove duplicate rows")
        null_option = st.selectbox(
            "Handle missing values",
            ["Do Nothing", "Drop rows with nulls", "Fill numeric with 0 & text with 'Unknown'"]
        )

        if st.button("Apply Cleaning"):

            clean_df = df.copy()

            if drop_dupes:
                clean_df = clean_df.drop_duplicates()

            if null_option == "Drop rows with nulls":
                clean_df = clean_df.dropna()

            elif null_option == "Fill numeric with 0 & text with 'Unknown'":
                num_cols = clean_df.select_dtypes(include=["number"]).columns
                obj_cols = clean_df.select_dtypes(exclude=["number"]).columns
                clean_df[num_cols] = clean_df[num_cols].fillna(0)
                clean_df[obj_cols] = clean_df[obj_cols].fillna("Unknown")

            st.session_state.cleaned_df = clean_df
            st.success("Cleaning complete.")

        if st.session_state.cleaned_df is not None:

            st.subheader("Preview of Cleaned Data")
            st.dataframe(st.session_state.cleaned_df.head(), use_container_width=True)

            csv = st.session_state.cleaned_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Download Cleaned CSV",
                data=csv,
                file_name="guardian_cleaned_data.csv",
                mime="text/csv",
                type="primary"
            )

else:
    st.info("Upload a dataset or load the enterprise sample dataset to begin.")
