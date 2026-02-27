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
# Initialize Session State
# -----------------------------
if "use_sample_data" not in st.session_state:
    st.session_state.use_sample_data = False
if "cleaned_df" not in st.session_state:
    st.session_state.cleaned_df = None

# -----------------------------
# Sidebar - File Upload & Sample
# -----------------------------
st.sidebar.header("Configuration")

if st.sidebar.button("🧪 Load Sample Data"):
    st.session_state.use_sample_data = True
    st.session_state.cleaned_df = None # Reset clean data on new load

st.sidebar.markdown("**OR**")

uploaded_file = st.sidebar.file_uploader("Upload CSV Dataset", type=["csv"])

if uploaded_file is not None:
    st.session_state.use_sample_data = False
    st.session_state.cleaned_df = None

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
        st.sidebar.success("Using Virtual Sample Data")
        df = pd.DataFrame({
            "Transaction_ID": [101, 102, 103, 104, 105, 105], 
            "Revenue": [1500, 2300, -50, 4100, 99999, 99999], 
            "Cost": [1000, 2500, 20, 3000, 50000, 50000], 
            "Date": ["2023-01-01", "2023-01-02", None, "2023-01-04", "2023-01-05", "2023-01-05"], 
            "Category": ["Tech", "Home", "Tech", "Toys", "Tech", "Tech"]
        })

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# -----------------------------
# Main App Logic
# -----------------------------
if df is not None:
    auditor = GuardianAuditor(df)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Audit Settings")

    numeric_columns_available = df.select_dtypes(include=["number"]).columns.tolist()

    numeric_cols = st.sidebar.multiselect(
        "Select Numeric Columns for Validity/Accuracy Check",
        numeric_columns_available,
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
    default_a = col_list.index("Revenue") if st.session_state.use_sample_data else 0
    col_a = st.sidebar.selectbox("Select Column A", col_list, index=default_a)

    default_b = col_list.index("Cost") if st.session_state.use_sample_data else (1 if len(col_list) > 1 else 0)
    col_b = st.sidebar.selectbox("Select Column B", col_list, index=default_b)

    # Run Checks
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

    # Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall Data Health", f"{overall_score:.1f}%")
    col2.metric("Total Records", len(df))
    col3.metric("Duplicate Rows", dupe_count)
    col4.metric("Missing Values", sum(completeness_dict.values()) if completeness_dict else 0)

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Profiling & Completeness",
        "🧪 Validity & Dupes",
        "🎯 Accuracy & Consistency",
        "🗂️ Data View",
        "🧹 Remediation (Fix Data)"
    ])

    # TAB 1: PROFILING & COMPLETENESS
    with tab1:
        st.write("### Missing Values")
        if completeness_dict:
            null_df = pd.DataFrame(list(completeness_dict.items()), columns=["Column", "Missing Count"])
            fig = px.bar(null_df, x="Column", y="Missing Count", color="Missing Count", color_continuous_scale="Reds")
            st.plotly_chart(fig, use_container_width=True)
        
        st.write("### Data Types & Unique Values")
        schema_df = pd.DataFrame({
            "Data Type": df.dtypes.astype(str),
            "Unique Values": df.nunique(),
            "Memory Usage (Bytes)": df.memory_usage(deep=True)[1:]
        })
        st.dataframe(schema_df, use_container_width=True)

    # TAB 2: VALIDITY & DUPES
    with tab2:
        col_left, col_right = st.columns(2)
        with col_left:
            st.write("### Uniqueness Check")
            if dupe_count > 0:
                st.error(f"Found {dupe_count} duplicate rows.")
            else:
                st.success("No duplicates detected!")

        with col_right:
            st.write("### Validity (Negative Value Check)")
            if numeric_cols:
                st.json(validity_results)
            else:
                st.info("Select numeric columns in sidebar.")

    # TAB 3: ACCURACY & CONSISTENCY
    with tab3:
        st.write("### Accuracy (Outlier Detection)")
        if numeric_cols:
            fig_box = px.box(df, y=numeric_cols, title="Outlier Visualization", template="plotly_dark")
            st.plotly_chart(fig_box, use_container_width=True)
            st.json(outlier_results)
        else:
            st.info("Select numeric columns to see outliers.")
            
    # TAB 4: DATA VIEW
    with tab4:
        st.dataframe(df, use_container_width=True)

    # TAB 5: REMEDIATION (NEW)
    with tab5:
        st.write("### Clean Your Data")
        st.markdown("Select operations to apply to your dataset, then download the cleaned version.")
        
        col_a, col_b = st.columns(2)
        with col_a:
            drop_dupes = st.checkbox("Drop Duplicate Rows")
            handle_nulls = st.selectbox("Handle Missing Values", ["Do Nothing", "Drop Rows with Nulls", "Fill with 'Unknown' or 0"])
        
        if st.button("Apply Cleaning Rules"):
            clean_df = df.copy()
            
            if drop_dupes:
                clean_df = clean_df.drop_duplicates()
                
            if handle_nulls == "Drop Rows with Nulls":
                clean_df = clean_df.dropna()
            elif handle_nulls == "Fill with 'Unknown' or 0":
                # Fill numbers with 0, objects with "Unknown"
                num_cols = clean_df.select_dtypes(include=['number']).columns
                obj_cols = clean_df.select_dtypes(exclude=['number']).columns
                clean_df[num_cols] = clean_df[num_cols].fillna(0)
                clean_df[obj_cols] = clean_df[obj_cols].fillna("Unknown")
            
            st.session_state.cleaned_df = clean_df
            st.success("Data cleaned successfully!")

        if st.session_state.cleaned_df is not None:
            st.write("#### Preview of Cleaned Data")
            st.dataframe(st.session_state.cleaned_df.head())
            
            # Export functionality
            csv = st.session_state.cleaned_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Cleaned CSV",
                data=csv,
                file_name="guardian_cleaned_data.csv",
                mime="text/csv",
                type="primary"
            )

else:
    st.info("Please upload a CSV file or load the sample dataset to begin auditing.")
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=2070", 
             caption="Upload a dataset to generate a Data Health Report",
             use_container_width=True)
