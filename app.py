# app.py

import streamlit as st
import json
from pathlib import Path
from utils import load_from_drive, backup_to_drive, secure_filename

# Set Streamlit page config
st.set_page_config(page_title="Patent Summary Tool", layout="wide")

st.title("🧠 Patent Application Summary Tool")
st.info("Navigate through the pages in the sidebar to edit claims, extract features, create a network, and generate a summary document.")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# File input (no longer listing everything)
current_filename = st.session_state.get("filename", None)
raw_input = st.text_input("Enter a new filename or reuse session one:", value=current_filename or "", placeholder="e.g., EP1234567")

if not raw_input:
    st.stop()

filename = secure_filename(raw_input)
st.session_state["filename"] = filename

summary_path = DATA_DIR / filename / f"Summary_{filename}.json"
(DATA_DIR / filename).mkdir(parents=True, exist_ok=True)

# Load local file
if summary_path.exists():
    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            st.session_state["summary_data"] = json.load(f)
    except Exception as e:
        st.warning(f"⚠️ Failed to load local JSON file: {e}")
        st.session_state["summary_data"] = {}
else:
    st.session_state["summary_data"] = {}

# Load from Google Drive
if st.button("☁️ Load from Google Drive", use_container_width=True):
    try:
        data = load_from_drive(filename)
        st.session_state["summary_data"] = data
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        st.success("✅ Loaded data from Google Drive.")
    except Exception as e:
        st.error(f"❌ Failed to load from Drive: {e}")

# Download
if st.session_state.get("summary_data"):
    json_str = json.dumps(st.session_state["summary_data"], indent=4, ensure_ascii=False)
    st.download_button(
        label="📥 Download Summary JSON",
        data=json_str,
        file_name=f"Summary_{filename}.json",
        mime="application/json",
        use_container_width=True
    )

# Backup to Drive
if st.button("📤 Backup to Google Drive", use_container_width=True):
    try:
        backup_to_drive(filename, st.session_state["summary_data"])
        st.success("✅ Backup completed to Google Drive.")
    except Exception as e:
        st.error(f"❌ Failed to upload to Drive: {e}")
