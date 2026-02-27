import streamlit as st
import pandas as pd
import plotly.express as px
from model import GuardianAuditor
import numpy as np

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
# Initialize Session State
# -----------------------------
# We use this to remember if the user clicked the sample data button
if "use_sample_data" not in st.session_state:
    st.session_state.use_sample_data = False

# -----------------------------
# Sidebar - File Upload & Sample
# -----------------------------
st.sidebar.header("Configuration")

# 1. Option to use sample data
if st.sidebar.button("🧪 Load Sample Data"):
    st.session_state.use_sample_data = True

st.sidebar.markdown("**OR**")

# 2. Option to upload custom data
uploaded_file = st.sidebar.file_uploader("Upload CSV Dataset", type=["csv"])

# If a user uploads a file, turn off the sample data mode
if uploaded_file is not None:
    st.session_state.use_sample_data = False

# -----------------------------
# Data Loading Logic
# -----------------------------
df = None

try:
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if df.empty:
            st.error("Uploaded file is empty.")
            st.stop()
            
    elif st.session_state.use_sample_data:
        # Generate a virtual dataset with intentional quality issues
        st.sidebar.success("Using Virtual Sample Data")
        df = pd.DataFrame({
            "Transaction_ID": [101, 102, 103, 104, 105, 105], # Duplicate ID
            "Revenue": [1500, 2300, -50, 4100, 99999, 99999], # Negative value & massive outlier
            "Cost": [1000, 2500, 20, 3000, 50000, 50000], # Cost > Revenue anomaly for consistency check
            "Date": ["2023-01-01", "2023-01-02", None, "2023-01-04", "2023-01-05", "2023-01-05"], # Missing value
            "Category": ["Tech", "Home", "Tech", "Toys", "Tech", "Tech"]
        })

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# -----------------------------
# Main App Logic (Only runs if data exists)
# -----------------------------
if df is not None:
    auditor = GuardianAuditor(df)

    # -----------------------------
    # Sidebar Settings
    # -----------------------------
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Audit Settings")

    numeric_columns_available = df.select_dtypes(include=["number"]).columns.tolist()

    numeric_cols = st.sidebar.multiselect(
        "Select Numeric Columns for Validity/Accuracy Check",
        numeric_columns_available,
        # Default selection for better UX if using sample data
        default=["Revenue", "Cost"] if st.session_state.use_sample_data else None
    )

    date_col = st.sidebar.selectbox(
        "Select Date Column for Timeliness Check",
        ["None"] + df.columns.tolist(),
        index=df.columns.tolist().index("Date") + 1 if st.session_state.use_sample_data else 0
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Consistency Rules")
    st.sidebar.info("Rule: Column A should be >= Column B")

    col_list = df.columns.tolist()

    # Pre-select columns for consistency check if using sample data
    default_a = col_list.index("Revenue") if st.session_state.use_sample_data else 0
    col_a = st.sidebar.selectbox("Select Column A", col_list, index=default_a)

    default_b = col_list.index("Cost") if st.session_state.use_sample_data else (1 if len(col_list) > 1 else 0)
    col_b = st.sidebar.selectbox("Select Column B", col_list, index=default_b)

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
            st.write("#### Statistical Distribution")
            fig_box = px.box(df, y=numeric_cols, 
                             title="Outlier Visualization (Box & Whiskers)",
                             template="plotly_dark",
                             color_discrete_sequence=['#00CC96'])
            st.plotly_chart(fig_box, use_container_width=True)
            
            st.write("#### Raw Outlier Counts")
            st.json(outlier_results)
        else:
            st.info("Select numeric columns in sidebar to see distribution and outliers.")
            
    # -----------------------------
    # TAB 4: DATA VIEW
    # -----------------------------
    with tab4:
        st.dataframe(df)

else:
    # This is what the user sees BEFORE uploading or clicking sample data
    st.info("Please upload a CSV file or load the sample dataset to begin auditing.")
    
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=2070", 
             caption="Upload a dataset to generate a C.C.U.V.A.T. Health Report",
             use_container_width=True)
