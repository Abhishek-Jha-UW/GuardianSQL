import streamlit as st
import pandas as pd
import plotly.express as px
from model import GuardianAuditor

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="GuardianSQL | Data Quality Auditor",
    layout="wide"
)

st.title("🛡️ GuardianSQL")
st.subheader("Automated Data Quality & Governance Auditor")
st.markdown("---")

# -----------------------------
# Sidebar - File Upload
# -----------------------------
st.sidebar.header("Configuration")
uploaded_file = st.sidebar.file_uploader("Upload CSV Dataset", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        if df.empty:
            st.error("Uploaded file is empty.")
            st.stop()

        auditor = GuardianAuditor(df)

    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()

    # -----------------------------
    # Sidebar Settings
    # -----------------------------
    st.sidebar.markdown("### Audit Settings")

    numeric_columns_available = df.select_dtypes(include=["number"]).columns.tolist()

    numeric_cols = st.sidebar.multiselect(
        "Select Numeric Columns for Validity/Accuracy Check",
        numeric_columns_available
    )

    date_col = st.sidebar.selectbox(
        "Select Date Column for Timeliness Check",
        ["None"] + df.columns.tolist()
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Consistency Rules")
    st.sidebar.info("Rule: Column A should be >= Column B")

    col_list = df.columns.tolist()

    col_a = st.sidebar.selectbox("Select Column A", col_list, index=0)

    # Safe index for second column
    col_b_index = 1 if len(col_list) > 1 else 0
    col_b = st.sidebar.selectbox("Select Column B", col_list, index=col_b_index)

    # -----------------------------
    # Run Checks
    # -----------------------------
    completeness_dict = auditor.check_completeness()
    dupe_count = auditor.check_uniqueness()

    validity_results = {}
    outlier_results = {}

    if numeric_cols:
        validity_results = auditor.check_validity(numeric_cols)
        outlier_results = auditor.check_accuracy(numeric_cols)

    if date_col != "None":
        auditor.check_timeliness(date_col)

    inc_count = auditor.check_consistency(col_a, col_b)
    overall_score = auditor.get_overall_health_score()

    # -----------------------------
    # Top Metrics
    # -----------------------------
    col1, col2, col3 = st.columns(3)

    col1.metric("Overall Data Health", f"{overall_score:.1f}%")
    col2.metric("Total Records", len(df))
    col3.metric("Duplicate Rows", dupe_count)

    st.markdown("---")

    # -----------------------------
    # Tabs
    # -----------------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Completeness",
        "🧪 Validity & Dupes",
        "🎯 Accuracy & Consistency",
        "🗂️ Data View"
    ])

    # -----------------------------
    # TAB 1: COMPLETENESS
    # -----------------------------
    with tab1:
        st.write("### Missing Values by Column")

        if completeness_dict:
            null_df = pd.DataFrame(
                list(completeness_dict.items()),
                columns=["Column", "Completeness %"]
            )

            fig = px.bar(
                null_df,
                x="Column",
                y="Completeness %",
                color="Completeness %",
                color_continuous_scale="RdYlGn"
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available.")

    # -----------------------------
    # TAB 2: VALIDITY & DUPES
    # -----------------------------
    with tab2:
        col_left, col_right = st.columns(2)

        with col_left:
            st.write("### Uniqueness Check")
            if dupe_count > 0:
                st.warning(f"Found {dupe_count} duplicate rows.")
            else:
                st.success("No duplicates detected!")

        with col_right:
            st.write("### Validity (Negative Value Check)")
            if numeric_cols:
                st.json(validity_results)
            else:
                st.info("Select numeric columns in sidebar.")

    # -----------------------------
    # TAB 3: ACCURACY & CONSISTENCY
    # -----------------------------
    with tab3:
        st.write("### Accuracy (Outlier Detection)")

        if numeric_cols:
            st.json(outlier_results)
        else:
            st.info("Select numeric columns in sidebar.")

        st.markdown("---")
        st.write(f"### Consistency Check: {col_a} vs {col_b}")

        if inc_count > 0:
            st.error(
                f"Inconsistency Found: {inc_count} rows where "
                f"{col_a} < {col_b}"
            )
        else:
            st.success("No inconsistencies found.")

    # -----------------------------
    # TAB 4: DATA VIEW
    # -----------------------------
    with tab4:
        st.dataframe(df.head(10))

else:
    # This is what the user sees BEFORE uploading
    st.info("Please upload a CSV file to begin auditing.")
    
    # You can use a URL for a clean tech/data related image
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=2070", 
             caption="Upload a dataset to generate a C.C.U.V.A.T. Health Report",
             use_container_width=True)
