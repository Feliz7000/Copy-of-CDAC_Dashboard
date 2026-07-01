import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from model_store import FINAL_MODEL_PATH, load_bundle

st.set_page_config(
    page_title="Placement Predictor Test Interface",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
<style>
    .main-title {
        font-size: 36px;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 5px;
        font-family: 'Inter', sans-serif;
    }
    .subtitle {
        font-size: 16px;
        color: #475569;
        margin-bottom: 25px;
        font-family: 'Inter', sans-serif;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">Student Placement Status Predictor</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Test interface to evaluate the trained machine learning model and placement cutoffs by uploading student scores.</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# PLACEMENT CRITERIA DIAGNOSTIC FUNCTIONS
# -----------------------------------------------------------------------------

def check_ccee(row):
    fails = []
    total_score = 0
    entered_count = 0
    for i in range(1, 9):
        col = f"cc_test_{i:02d}"
        val = row.get(col)
        if pd.isna(val):
            continue
        entered_count += 1
        val = float(val)
        total_score += val
        if val == 0:
            fails.append(f"test_{i:02d} (0)")
        elif val < 16:
            fails.append(f"test_{i:02d} ({val:.0f} < 16)")
    
    if entered_count == 0:
        return "Not Taken"
        
    pct = (total_score / 320.0) * 100.0
    if pct < 65.0:
        fails.append(f"Overall ({pct:.1f}% < 65.0%)")
        
    if fails:
        return ", ".join(fails)
    return "Met"

def check_ia(row):
    fails = []
    total_score = 0
    entered_count = 0
    for i in range(1, 9):
        col = f"ia_test_{i:02d}"
        val = row.get(col)
        if pd.isna(val):
            continue
        entered_count += 1
        val = float(val)
        total_score += val
        if val == 0:
            fails.append(f"test_{i:02d} (0)")
        elif val < 24:
            fails.append(f"test_{i:02d} ({val:.0f} < 24)")
            
    if entered_count == 0:
        return "Not Taken"
        
    pct = (total_score / 480.0) * 100.0
    if pct < 65.0:
        fails.append(f"Overall ({pct:.1f}% < 65.0%)")
    if fails:
        return ", ".join(fails)
    return "Met"

def check_aptitude(row):
    fails = []
    entered_count = 0
    for i in range(1, 21):
        col = f"ap_test_{i:02d}"
        val = row.get(col)
        if pd.isna(val):
            continue
        entered_count += 1
        val = float(val)
        if val == 0 and i in (1, 2):
            fails.append(f"test_{i:02d} (0)")
        elif val < 48:
            fails.append(f"test_{i:02d} ({val:.0f} < 48)")
            
    if entered_count == 0:
        return "Not Taken"
    if fails:
        return ", ".join(fails)
    return "Met"

def check_speakx(row):
    fails = []
    entered_count = 0
    for i in range(1, 11):
        col = f"sx_test_{i:02d}"
        val = row.get(col)
        if pd.isna(val):
            continue
        entered_count += 1
        val = float(val)
        if val == 0 and i in (1, 2):
            fails.append(f"test_{i:02d} (0)")
        elif val < 30:
            fails.append(f"test_{i:02d} ({val:.0f} < 30)")
            
    if entered_count == 0:
        return "Not Taken"
    if fails:
        return ", ".join(fails)
    return "Met"

def check_personality(row):
    total_score = 0
    entered_count = 0
    for i in range(1, 11):
        col = f"ps_test_{i:02d}"
        val = row.get(col)
        if pd.isna(val):
            continue
        entered_count += 1
        total_score += float(val)
        
    if entered_count == 0:
        return "Not Taken"
        
    pct = (total_score / 100.0) * 100.0
    if pct < 50.0:
        return f"Overall ({pct:.1f}% < 50.0%)"
    return "Met"

def check_grooming(row):
    total_score = 0
    entered_count = 0
    for i in range(1, 11):
        col = f"gr_test_{i:02d}"
        val = row.get(col)
        if pd.isna(val):
            continue
        entered_count += 1
        total_score += float(val)
        
    if entered_count == 0:
        return "Not Taken"
        
    pct = (total_score / 100.0) * 100.0
    if pct < 50.0:
        return f"Overall ({pct:.1f}% < 50.0%)"
    return "Met"

def check_technical(row):
    fails = []
    total_score = 0
    entered_count = 0
    for i in range(1, 6):
        col = f"ta_test_{i:02d}"
        val = row.get(col)
        if pd.isna(val):
            continue
        entered_count += 1
        val = float(val)
        total_score += val
        if val == 0 and i in (1, 2):
            fails.append(f"test_{i:02d} (0)")
        elif val < 4:
            fails.append(f"test_{i:02d} ({val:.0f} < 4)")
            
    if entered_count == 0:
        return "Not Taken"
        
    pct = (total_score / 50.0) * 100.0
    if pct < 40.0:
        fails.append(f"Overall ({pct:.1f}% < 40.0%)")
    if fails:
        return ", ".join(fails)
    return "Met"

def check_numerical(row):
    fails = []
    total_score = 0
    entered_count = 0
    for i in range(1, 6):
        col = f"na_test_{i:02d}"
        val = row.get(col)
        if pd.isna(val):
            continue
        entered_count += 1
        val = float(val)
        total_score += val
        if val == 0 and i in (1, 2):
            fails.append(f"test_{i:02d} (0)")
        elif val < 4:
            fails.append(f"test_{i:02d} ({val:.0f} < 4)")
            
    if entered_count == 0:
        return "Not Taken"
        
    pct = (total_score / 50.0) * 100.0
    if pct < 40.0:
        fails.append(f"Overall ({pct:.1f}% < 40.0%)")
    if fails:
        return ", ".join(fails)
    return "Met"

def check_interview(row):
    fails = []
    entered_count = 0
    for i in range(1, 6):
        col = f"in_test_{i:02d}"
        val = row.get(col)
        if pd.isna(val):
            continue
        entered_count += 1
        val = float(val)
        if val == 0 and i in (1, 2):
            fails.append(f"test_{i:02d} (0)")
        elif val < 8:
            fails.append(f"test_{i:02d} ({val:.0f} < 8)")
            
    if entered_count == 0:
        return "Not Taken"
    if fails:
        return ", ".join(fails)
    return "Met"

def check_as(row):
    entered = sum(1 for i in range(1, 31) if not pd.isna(row.get(f"as_test_{i:02d}")))
    if entered == 0:
        return "Not Taken"
    if entered < 25:
        return f"Completed ({entered} < 25)"
    return "Met"

def check_pq(row):
    entered = sum(1 for i in range(1, 31) if not pd.isna(row.get(f"pq_test_{i:02d}")))
    if entered == 0:
        return "Not Taken"
    if entered < 30:
        return f"Completed ({entered} < 30)"
    return "Met"

def check_gac(row):
    val = row.get("gac_test_01")
    if pd.isna(val):
        return "Not Taken"
    if float(val) == 0:
        return "gac_test_01 (0)"
    return "Met"

def check_project(row):
    val = row.get("prj_test_01")
    if pd.isna(val):
        return "Not Taken"
    if float(val) == 0:
        return "prj_test_01 (0)"
    return "Met"

def analyze_row_categories(row):
    return {
        "Aptitude (AP)": check_aptitude(row),
        "Aptitude Skill (AS)": check_as(row),
        "CCEE (CC)": check_ccee(row),
        "GAC": check_gac(row),
        "Grooming (GR)": check_grooming(row),
        "Interview (IN)": check_interview(row),
        "Internal Assessment (IA)": check_ia(row),
        "Numerical Aptitude (NA)": check_numerical(row),
        "Personality & Quantitative (PQ)": check_pq(row),
        "Project (PRJ)": check_project(row),
        "Personality (PS)": check_personality(row),
        "Speak X (SX)": check_speakx(row),
        "Technical Assessment (TA)": check_technical(row),
    }

# -----------------------------------------------------------------------------
# ACTUAL LABELS PARSING & NORMALIZATION
# -----------------------------------------------------------------------------

def extract_actual_labels(df):
    known_cols = ["placement_status", "status", "placement status", "result", "actual status", "actual_status", "placement_ready"]
    for c in df.columns:
        if str(c).strip().lower() in known_cols:
            return df[c].tolist(), str(c)
            
    # Check if any column contains common placement keywords
    common_values = {"placement ready", "can improve", "not placement ready", "eligible", "hold", "not eligible", "np", "pass", "fail"}
    for c in df.columns:
        unique_vals = set(df[c].dropna().astype(str).str.strip().str.lower().unique())
        if unique_vals.intersection(common_values):
            return df[c].tolist(), str(c)
            
    # Fallback to the first column
    return df.iloc[:, 0].tolist(), df.columns[0]

def clean_status_label(val):
    if pd.isna(val):
        return "Unknown"
    raw = str(val).strip().lower()
    aliases = {
        "np": "Placement ready",
        "eligible": "Placement ready",
        "placement ready": "Placement ready",
        "hold": "Can Improve",
        "can improve": "Can Improve",
        "not eligible": "Not Placement ready",
        "not placement ready": "Not Placement ready",
        "fail": "Not Placement ready",
        "pass": "Placement ready"
    }
    return aliases.get(raw, str(val).strip())

# -----------------------------------------------------------------------------
# MODEL LOADING
# -----------------------------------------------------------------------------

MODEL_PATH = FINAL_MODEL_PATH

@st.cache_resource
def load_model_bundle():
    bundle = load_bundle()
    if bundle is None:
        st.error(f"Trained model not found at {MODEL_PATH}. Please train the model first.")
        return None
    return bundle

bundle = load_model_bundle()

if bundle is None:
    st.info(f"Train or incrementally update the model at `{FINAL_MODEL_PATH}`.")
else:
    model = bundle["model"]
    preprocessor = bundle["preprocessor"]
    selected_raw_columns = bundle["selected_raw_columns"]
    label_map = bundle["label_map"]
    
    # Reverse label map for predictions
    code_to_label = {
        0: "Not Placement ready",
        1: "Can Improve",
        2: "Placement ready"
    }

    # Load a few sample rows to populate the template
    @st.cache_data
    def generate_template_csv():
        csv_path = Path("data/raw/placement_Feb25_corrected_updated.csv")
        if csv_path.exists():
            df_raw = pd.read_csv(csv_path)
            # Take first 3 rows as sample
            sample_df = df_raw.head(3).copy()
        else:
            # Create a mock student row as fallback
            sample_df = pd.DataFrame([{
                "prn": "123456789012",
                "student_full_name": "John Doe",
                "batch_name": "August 2024"
            }])
            
        # Ensure all selected feature columns exist in the template
        for col in selected_raw_columns:
            if col not in sample_df.columns:
                sample_df[col] = np.nan
                
        # Arrange columns: prn, student_full_name, batch_name, followed by features
        id_cols = [c for c in ["prn", "student_full_name", "batch_name"] if c in sample_df.columns]
        feature_cols = [c for c in selected_raw_columns if c not in id_cols]
        final_cols = id_cols + feature_cols
        
        # Drop model target/inference columns if they exist in raw
        drop_cols = ["placement_status", "pass_fail"]
        final_cols = [c for c in final_cols if c not in drop_cols]
        
        return sample_df[final_cols]

    template_df = generate_template_csv()
    template_csv = template_df.to_csv(index=False).encode('utf-8')

    # Sidebar / Download Section
    with st.sidebar:
        st.header("Download Template")
        st.write("Download the template CSV with all 143 evaluation columns, fill in some marks, and upload it on the right.")
        st.download_button(
            label="Download CSV Template",
            data=template_csv,
            file_name="placement_template.csv",
            mime="text/csv"
        )
        st.write("---")
        st.markdown("""
        ### Instructions:
        1. Keep the `prn` and `student_full_name` columns.
        2. Enter scores for the tests you want to evaluate.
        3. You can **leave columns blank** for tests that were not taken. The model's imputer will automatically handle them.
        """)

    # Main Upload Section
    st.header("Upload Filled Template")
    
    col_upload1, col_upload2 = st.columns(2)
    with col_upload1:
        uploaded_file = st.file_uploader("Upload your filled placement CSV/Excel file (Student Marks)", type=["csv", "xlsx", "xls"])
    with col_upload2:
        uploaded_actuals_file = st.file_uploader("Upload Actual Placement Results CSV/Excel (Optional for Accuracy Evaluation)", type=["csv", "xlsx", "xls"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(('.xlsx', '.xls')):
                input_df = pd.read_excel(uploaded_file)
            else:
                input_df = pd.read_csv(uploaded_file)
            
            # Automatically rename the first column to 'prn' if it's unnamed or blank
            if len(input_df.columns) > 0:
                first_col_name = str(input_df.columns[0]).strip()
                if first_col_name.startswith("Unnamed:") or first_col_name == "":
                    input_df.rename(columns={input_df.columns[0]: "prn"}, inplace=True)
                    
            st.success("Marks file uploaded successfully!")
            
            # Read actual status if provided
            actuals_df = None
            if uploaded_actuals_file is not None:
                if uploaded_actuals_file.name.endswith(('.xlsx', '.xls')):
                    actuals_df = pd.read_excel(uploaded_actuals_file)
                else:
                    actuals_df = pd.read_csv(uploaded_actuals_file)
                st.success("Actual status file uploaded successfully!")
            
            # Show preview of uploaded file
            st.subheader("Data Preview (First 5 Rows)")
            st.dataframe(input_df.head(5), width='stretch')
            
            # Run Predictions
            if st.button("Run Placement Status Prediction", type="primary"):
                # Prepare features
                # Ensure all selected_raw_columns are present in the uploaded dataframe with exact order and numeric type
                features_dict = {}
                for col in selected_raw_columns:
                    if col in input_df.columns:
                        features_dict[col] = pd.to_numeric(input_df[col], errors='coerce')
                    else:
                        features_dict[col] = pd.Series(np.nan, index=input_df.index)
                df_features = pd.DataFrame(features_dict, index=input_df.index)
                
                # Run preprocessing
                X_transformed = preprocessor.transform(df_features)
                
                # Make predictions
                preds = model.predict(X_transformed)
                probs = model.predict_proba(X_transformed)
                
                # Map results
                results_df = input_df.copy()
                results_df["Predicted Status"] = [code_to_label[p] for p in preds]
                results_df["Confidence Score (%)"] = [round(float(prob[p]) * 100, 2) for prob, p in zip(probs, preds)]
                
                # Compute category-wise diagnostics
                diagnostics_list = []
                for _, row in input_df.iterrows():
                    diag = analyze_row_categories(row)
                    diagnostics_list.append(diag)
                
                # Concat diagnostic dataframe
                diags_df = pd.DataFrame(diagnostics_list, index=input_df.index)
                results_df = pd.concat([results_df, diags_df], axis=1)
                
                # Accuracy computation if actuals uploaded
                has_actuals = False
                accuracy_pct = 0.0
                correct_predictions = 0
                
                if actuals_df is not None:
                    actual_labels, actual_col_name = extract_actual_labels(actuals_df)
                    actuals_cleaned = [clean_status_label(x) for x in actual_labels]
                    
                    if len(actuals_cleaned) == len(input_df):
                        has_actuals = True
                        results_df["Actual Status"] = actuals_cleaned
                        results_df["Match?"] = ["✅ Yes" if p == a else "❌ No" for p, a in zip(results_df["Predicted Status"], actuals_cleaned)]
                        
                        correct_predictions = sum(p == a for p, a in zip(results_df["Predicted Status"], actuals_cleaned))
                        accuracy_pct = round(correct_predictions / len(actuals_cleaned) * 100, 2)
                    else:
                        st.error(f"Error: The actual results CSV ({len(actuals_cleaned)} rows) does not have the same number of rows as the marks CSV ({len(input_df)} rows). Accuracy calculation skipped.")
                
                # Shift columns to front for visibility
                category_cols = list(diags_df.columns)
                if has_actuals:
                    front_cols = ["prn", "student_full_name", "Predicted Status", "Actual Status", "Match?", "Confidence Score (%)"] + category_cols
                else:
                    front_cols = ["prn", "student_full_name", "Predicted Status", "Confidence Score (%)"] + category_cols
                
                # Make sure we only select columns that actually exist in the dataframe
                front_cols_exist = [c for c in front_cols if c in results_df.columns]
                other_cols = [c for c in results_df.columns if c not in front_cols_exist]
                results_df = results_df[front_cols_exist + other_cols]
                
                # Display Results
                st.subheader("Prediction Results")
                
                if has_actuals:
                    st.markdown(f"""
                    <div class="metric-card" style="border-left: 5px solid #2563EB; background-color: #EFF6FF; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
                        <span style="font-size: 14px; font-weight: 600; color: #1E40AF; text-transform: uppercase; letter-spacing: 0.05em;">Batch Evaluation Accuracy</span>
                        <h2 style="margin: 5px 0 2px 0; font-size: 36px; font-weight: 800; color: #1D4ED8;">{accuracy_pct}%</h2>
                        <span style="font-size: 14px; color: #1E40AF; font-weight: 500;">{correct_predictions} out of {len(results_df)} predictions matched the actual placement results.</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.write("Below is the styled prediction table. Category columns show exact areas where the student failed to meet placement requirements (with scores or completion counts).")
                
                # Highlight rows based on prediction status and category performance
                def style_cells(val):
                    if val == "Met" or val == "✅ Yes":
                        return 'background-color: #E6F4EA; color: #137333; font-weight: 500;'
                    elif val == "Placement ready":
                        return 'background-color: #D1FAE5; color: #065F46; font-weight: bold;'
                    elif val == "Can Improve":
                        return 'background-color: #FEF3C7; color: #92400E; font-weight: bold;'
                    elif val == "Not Placement ready" or val == "❌ No":
                        return 'background-color: #FEE2E2; color: #991B1B; font-weight: bold;'
                    elif val == "Not Taken":
                        return 'background-color: #F1F3F4; color: #5F6368; font-style: italic;'
                    elif isinstance(val, str) and ("<" in val or "(" in val):
                        return 'background-color: #FCE8E6; color: #C5221F; font-weight: 500;'
                    return ''
                
                subset_cols = ["Predicted Status"] + category_cols
                if has_actuals:
                    subset_cols = ["Predicted Status", "Actual Status", "Match?"] + category_cols
                    
                st.dataframe(
                    results_df.style.map(style_cells, subset=subset_cols),
                    width='stretch'
                )
                
                # Summary metrics
                st.subheader("Summary Statistics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    ready_count = int(sum(results_df["Predicted Status"] == "Placement ready"))
                    st.metric("Predicted: Placement Ready", ready_count)
                with col2:
                    improve_count = int(sum(results_df["Predicted Status"] == "Can Improve"))
                    st.metric("Predicted: Can Improve", improve_count)
                with col3:
                    not_ready_count = int(sum(results_df["Predicted Status"] == "Not Placement ready"))
                    st.metric("Predicted: Not Placement Ready", not_ready_count)
                
                if has_actuals:
                    st.subheader("Class-wise Accuracy")
                    classes = ["Placement ready", "Can Improve", "Not Placement ready"]
                    metrics = []
                    for c in classes:
                        actual_c = sum(results_df["Actual Status"] == c)
                        if actual_c > 0:
                            correct_c = sum((results_df["Actual Status"] == c) & (results_df["Predicted Status"] == c))
                            acc_c = correct_c / actual_c * 100
                            metrics.append({"Class": c, "Accuracy": f"{acc_c:.1f}%", "Details": f"{correct_c} / {actual_c} correctly predicted"})
                        else:
                            metrics.append({"Class": c, "Accuracy": "N/A", "Details": "0 actual samples in this class"})
                    st.table(pd.DataFrame(metrics))
                
                # Download results button
                results_csv = results_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Prediction & Evaluation Results",
                    data=results_csv,
                    file_name="predicted_placement_results.csv",
                    mime="text/csv"
                )
                
        except Exception as e:
            st.error(f"Error processing file: {e}")
            import traceback
            st.code(traceback.format_exc())
