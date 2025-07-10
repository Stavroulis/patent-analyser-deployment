# ✅ Optimized Streamlit App Entrypoint (app.py)
import streamlit as st
import json
from pathlib import Path
from utils import load_from_drive, backup_to_drive


# Set Streamlit page config
st.set_page_config(page_title="Patent Summary Tool", layout="wide")

st.title("🧠 Patent Application Summary Tool")
st.info("Navigate through the pages in the sidebar to edit claims, extract features, create a network, and generate a summary document.")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Get existing filenames
available_files = [f.name for f in DATA_DIR.iterdir() if f.is_dir()]
available_files.sort()
options = available_files + ["<Create New>"]

# Pre-select existing file if present
current_filename = st.session_state.get("filename", None)
if current_filename in options:
    index = options.index(current_filename)
else:
    index = len(options) - 1

filename = st.selectbox("Select existing file or type a new one:", options, index=index)

if filename == "<Create New>":
    filename = st.text_input("Enter a new filename:", placeholder="e.g., EP1234567")
    if not filename:
        st.stop()

# Store filename
st.session_state["filename"] = filename
summary_path = Path("data") / filename / f"Summary_{filename}.json"
(Path("data") / filename).mkdir(parents=True, exist_ok=True)

# Load summary data from local file if exists
if summary_path.exists():
    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            st.session_state["summary_data"] = json.load(f)
    except Exception as e:
        st.warning(f"⚠️ Failed to load local JSON file: {e}")
        st.session_state["summary_data"] = {}
else:
    st.session_state["summary_data"] = {}

# Manual sync from Drive (optional backup)
if st.button("☁️ Load from Google Drive", use_container_width=True):
    try:
        data = load_from_drive(filename)
        st.session_state["summary_data"] = data
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        st.success("✅ Loaded data from Google Drive.")
    except Exception as e:
        st.error(f"❌ Failed to load from Drive: {e}")

# Optional: download button
if st.session_state.get("summary_data"):
    json_str = json.dumps(st.session_state["summary_data"], indent=4, ensure_ascii=False)
    st.download_button(
        label="📥 Download Summary JSON",
        data=json_str,
        file_name=f"Summary_{filename}.json",
        mime="application/json",
        use_container_width=True
    )

# Manual backup to Drive
if st.button("📤 Backup to Google Drive", use_container_width=True):
    try:
        backup_to_drive(filename, st.session_state["summary_data"])
        st.success("✅ Backup completed to Google Drive.")
    except Exception as e:
        st.error(f"❌ Failed to upload to Drive: {e}")
