import streamlit as st
import pandas as pd
import plotly.express as px
from model import GuardianAuditor

# 1. Page Configuration
st.set_page_config(page_title="GuardianSQL | Data Quality Auditor", layout="wide")

st.title("🛡️ GuardianSQL")
st.subheader("Automated Data Quality & Governance Auditor")
st.markdown("---")

# 2. Sidebar - File Upload
st.sidebar.header("Configuration")
uploaded_file = st.sidebar.file_uploader("Upload CSV Dataset", type=["csv"])

if uploaded_file:
    # Load Data
    df = pd.read_csv(uploaded_file)
    auditor = GuardianAuditor(df)
    
    # 3. User Input for Specific Checks
    st.sidebar.markdown("### Audit Settings")
    
    # Validity & Accuracy Selection
    numeric_cols = st.sidebar.multiselect(
        "Select Numeric Columns for Validity/Accuracy Check", 
        df.select_dtypes(include=['number']).columns
    )
    
    # Timeliness Selection
    date_col = st.sidebar.selectbox(
        "Select Date Column for Timeliness Check", 
        [None] + list(df.columns)
    )

    # NEW: Consistency Selection (Moved here to affect Health Score)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Consistency Rules")
    st.sidebar.info("Rule: Column A should be >= Column B")
    col_a = st.sidebar.selectbox("Select Column A", df.columns, index=0)
    col_b = st.sidebar.selectbox("Select Column B", df.columns, index=1)

    # 4. Run C.C.U.V.A.T. Logic
    # These run first so the 'overall_score' is accurate
    null_stats = auditor.check_completeness()
    dupe_count = auditor.check_uniqueness()
    
    if numeric_cols:
        auditor.check_validity(numeric_cols)
        auditor.check_accuracy(numeric_cols)
        
    if date_col:
        auditor.check_timeliness(date_col)

    # This now uses the A >= B logic and updates report_summary
    inc_count = auditor.check_consistency(col_a, col_b)
    
    # FINALLY, calculate health score (Now it won't be 100% if errors exist!)
    overall_score = auditor.get_overall_health_score()

    # 5. Display Top-Level Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Overall Data Health", f"{overall_score:.1f}%")
    col2.metric("Total Records", len(df))
    col3.metric("Duplicate Rows", dupe_count)

    st.markdown("---")

    # 6. Detailed Analysis Tabs
    if numeric_cols:
        auditor.check_validity(numeric_cols)
        outlier_results = auditor.check_accuracy(numeric_cols) # New Accuracy Check

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Completeness", "🧪 Validity & Dupes", "🎯 Accuracy & Consistency", "🗂️ Data View"])
    
    with tab1:
        st.write("### Missing Values by Column")
        # Turn Series into DataFrame for Plotly
        null_df = null_stats.reset_index()
        null_df.columns = ['Column', 'Completeness %']
        fig = px.bar(null_df, x='Column', y='Completeness %', 
                     title="Data Completeness (Goal: 100%)",
                     color='Completeness %', color_continuous_scale='RdYlGn')
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col_left, col_right = st.columns(2)
        with col_left:
            st.write("### Uniqueness Check")
            if dupe_count > 0:
                st.warning(f"Found {dupe_count} duplicate rows.")
            else:
                st.success("No duplicate rows detected!")
        
        with col_right:
            st.write("### Validity (Negative Value Check)")
            if numeric_cols:
                validity_results = auditor.check_validity(numeric_cols)
                st.write(validity_results)
            else:
                st.info("Select numeric columns in the sidebar to run validity checks.")

    with tab3:
        st.write("### Accuracy (Outlier Detection)")
        if numeric_cols:
            st.write("Outliers detected (Values outside 1.5x IQR):")
            st.json(outlier_results)
        else:
            st.info("Select numeric columns to check for outliers.")

        st.markdown("---")
        st.write("### Consistency Check")
        col_a = st.selectbox("Primary Column (e.g., Total Units)", df.columns, key="ca")
        col_b = st.selectbox("Secondary Column (e.g., Units Added)", df.columns, key="cb")
        
        if st.button("Run Consistency Audit"):
            inc_count = auditor.check_consistency(col_a, col_b)
            if inc_count > 0:
                st.error(f"Inconsistency Found: {inc_count} rows where {col_a} is less than {col_b}.")
            else:
                st.success("Logic holds! No inconsistencies found.")

    with tab4:
        st.write("### Sample Data Snippet")
        st.dataframe(df.head(10))
