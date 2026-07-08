import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api_client import APIClient

st.set_page_config(page_title="Upload Data", page_icon="📁", layout="wide")

# ── Auth guard ─────────────────────────────────────────────
if not st.session_state.get("token"):
    st.warning("Please login first.")
    st.stop()

client = APIClient()

# ── Page header ────────────────────────────────────────────
st.title("📁 Upload Your Data")
st.markdown("Upload a CSV or Excel file to get started. Max 50MB.")
st.divider()


# ════════════════════════════════════════════════════════════
# SECTION 1 — FILE UPLOADER
# ════════════════════════════════════════════════════════════

uploaded_file = st.file_uploader(
    "Drag and drop your file here",
    type=["csv", "xlsx"],
    help="Supported formats: CSV, Excel (.xlsx)",
)

if uploaded_file is not None:
    with st.spinner(f"Uploading and analyzing '{uploaded_file.name}'..."):
        data, status = client.upload_dataset(
            uploaded_file.getvalue(),
            uploaded_file.name,
        )

    if status != 201:
        st.error(f"Upload failed: {data.get('message', 'Unknown error')}")
        st.stop()

    dataset = data["dataset"]
    cleaning_report = data["cleaning_report"]
    suggestions = data["suggestions"]

    # Save to session state for other pages to use
    st.session_state["current_dataset_id"] = dataset["id"]
    st.session_state["current_dataset_name"] = dataset["original_filename"]
    st.session_state["suggestions"] = suggestions

    st.success(f"✅ '{dataset['original_filename']}' uploaded successfully!")

    # ── Dataset summary ────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", f"{dataset['row_count']:,}")
    col2.metric("Columns", dataset["col_count"])
    col3.metric("File Type", dataset["file_type"].upper())
    col4.metric(
        "Issues Found",
        cleaning_report["total_issues"],
        delta="needs attention" if cleaning_report["total_issues"] > 0 else "clean!",
        delta_color="inverse" if cleaning_report["total_issues"] > 0 else "normal",
    )

    st.divider()

    # ════════════════════════════════════════════════════════
    # SECTION 2 — DATA PREVIEW
    # ════════════════════════════════════════════════════════

    st.subheader("📊 Data Preview")
    with st.spinner("Loading preview..."):
        preview_data, preview_status = client.get_preview(dataset["id"])

    if preview_status == 200:
        preview_df = pd.DataFrame(preview_data["rows"])
        st.dataframe(preview_df, use_container_width=True, height=300)
        st.caption(
            f"Showing first {len(preview_data['rows'])} of "
            f"{preview_data['total_rows']:,} total rows"
        )
    else:
        st.warning("Could not load preview.")

    st.divider()

    # ════════════════════════════════════════════════════════
    # SECTION 3 — CLEANING REPORT CARDS
    # ════════════════════════════════════════════════════════

    if cleaning_report["total_issues"] > 0:
        st.subheader("🧹 Data Quality Issues Found")
        st.markdown(
            f"We found **{cleaning_report['total_issues']} issue(s)** in your dataset. "
            "Choose how to handle each one:"
        )

        # Store user's cleaning choices in session state
        if "clean_config" not in st.session_state:
            st.session_state["clean_config"] = {
                "fill_missing": {},
                "remove_duplicates": False,
                "fix_negative_columns": [],
                "standardize_categories": [],
            }

        for issue in cleaning_report["issues"]:
            with st.container():
                col_left, col_right = st.columns([3, 1])

                with col_left:
                    # Icon per issue type
                    icons = {
                        "missing_values": "⚠️",
                        "duplicates": "🔁",
                        "negative_values": "➖",
                        "invalid_dates": "📅",
                        "inconsistent_categories": "🔤",
                    }
                    icon = icons.get(issue["issue_type"], "❗")
                    st.markdown(f"{icon} **{issue['description']}**")

                with col_right:
                    fix_key = f"fix_{issue['issue_type']}_{issue.get('column','')}"

                    if issue["issue_type"] == "missing_values":
                        choice = st.selectbox(
                            "Fix",
                            options=["skip", "fill_median", "fill_mean", "fill_mode", "drop_rows"],
                            key=fix_key,
                            label_visibility="collapsed",
                        )
                        if choice != "skip":
                            st.session_state["clean_config"]["fill_missing"][issue["column"]] = choice

                    elif issue["issue_type"] == "duplicates":
                        choice = st.selectbox(
                            "Fix",
                            options=["skip", "remove_duplicates"],
                            key=fix_key,
                            label_visibility="collapsed",
                        )
                        if choice == "remove_duplicates":
                            st.session_state["clean_config"]["remove_duplicates"] = True

                    elif issue["issue_type"] == "negative_values":
                        choice = st.selectbox(
                            "Fix",
                            options=["skip", "replace_with_zero"],
                            key=fix_key,
                            label_visibility="collapsed",
                        )
                        if choice == "replace_with_zero":
                            if issue["column"] not in st.session_state["clean_config"]["fix_negative_columns"]:
                                st.session_state["clean_config"]["fix_negative_columns"].append(issue["column"])

                    elif issue["issue_type"] == "inconsistent_categories":
                        choice = st.selectbox(
                            "Fix",
                            options=["skip", "standardize_titlecase"],
                            key=fix_key,
                            label_visibility="collapsed",
                        )
                        if choice == "standardize_titlecase":
                            if issue["column"] not in st.session_state["clean_config"]["standardize_categories"]:
                                st.session_state["clean_config"]["standardize_categories"].append(issue["column"])

                    else:
                        st.markdown("—")

        st.markdown("")

        col_fix, col_skip = st.columns([1, 3])
        with col_fix:
            apply_button = st.button(
                "✅ Apply All Fixes",
                type="primary",
                use_container_width=True,
            )

        if apply_button:
            config = st.session_state["clean_config"]
            with st.spinner("Cleaning your data..."):
                clean_data, clean_status = client.clean_dataset(dataset["id"], config)

            if clean_status == 200:
                # Update session state to use the cleaned dataset
                st.session_state["current_dataset_id"] = clean_data["cleaned_dataset_id"]
                st.success(
                    f"✅ Data cleaned! "
                    f"{clean_data['rows_before']:,} → {clean_data['rows_after']:,} rows"
                )
                st.markdown("**Changes applied:**")
                for change in clean_data["changes_applied"]:
                    st.markdown(f"- {change}")
            else:
                st.error(f"Cleaning failed: {clean_data.get('message', 'Unknown error')}")

    else:
        st.success("✅ No data quality issues found. Your data is clean!")

    st.divider()

    # ════════════════════════════════════════════════════════
    # SECTION 4 — AI SUGGESTED QUESTIONS
    # ════════════════════════════════════════════════════════

    st.subheader("💡 AI-Suggested Questions")
    st.markdown(
        "Based on your data, here are some questions you can ask. "
        "Click one to go straight to the AI Chat:"
    )

    if suggestions:
        cols = st.columns(min(len(suggestions), 3))
        for i, question in enumerate(suggestions):
            col_idx = i % 3
            with cols[col_idx]:
                if st.button(
                    f"💬 {question}",
                    key=f"suggestion_{i}",
                    use_container_width=True,
                ):
                    st.session_state["prefill_question"] = question
                    st.switch_page("pages/2_Chat.py")
    else:
        st.info("No suggestions available yet.")

    st.divider()

    # ── Past uploads ───────────────────────────────────────
    st.subheader("📂 Your Previous Uploads")
    datasets_data, ds_status = client.list_datasets()
    if ds_status == 200 and datasets_data:
        for ds in datasets_data:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            col1.markdown(f"**{ds['original_filename']}**")
            col2.markdown(f"{ds['row_count']:,} rows" if ds['row_count'] else "—")
            col3.markdown(f"`{ds['status']}`")
            if col4.button("Use", key=f"use_{ds['id']}", use_container_width=True):
                st.session_state["current_dataset_id"] = ds["id"]
                st.session_state["current_dataset_name"] = ds["original_filename"]
                st.success(f"Switched to '{ds['original_filename']}'")
    else:
        st.info("No previous uploads yet.")