import streamlit as st
import re
from utils import secure_filename 

# --- Session Checks ---
if "filename" not in st.session_state:
    st.warning("No file selected. Please go to the main page.")
    st.stop()

filename = secure_filename(st.session_state["filename"])  # ✅ sanitize
data = st.session_state.get("summary_data", {})

st.title(f"Citations for Claim 1 – {filename}")

# --- Extract Data ---
comm_text = data.get("User Entered Claims", {}).get("Cl_1", "")
cl_1_list = data.get("Edited Feature Table", {}).get("Cl_1", [])

if not comm_text:
    st.warning("⚠️ Claim 1 text not available.")
    st.stop()

if not cl_1_list:
    st.warning("⚠️ No extracted features for Claim 1. Please process claims in '2_Extract Features'.")
    st.stop()

# --- Citation Injection Function ---
def cit_claim(comm_text):
    pattern = r'\b(' + '|'.join(map(re.escape, cl_1_list)) + r')\b'

    def replacement(match):
        matched_text = match.group(0)
        citation = " (D1: abstr., fig., page )"
        match_end = match.end()
        if match_end < len(comm_text) and comm_text[match_end] in ".,;:":
            return f"{matched_text}{citation}"
        return f"{matched_text}{citation}"

    updated_text = re.sub(pattern, replacement, comm_text, count=0)
    updated_text = re.sub(r"^[^a-zA-Z]+", "", updated_text)
    updated_text = re.sub(r"\)([.,;:]?)", r")\1\n", updated_text)
    updated_text = re.sub(r"([.,;:]) (\b(?:a|an)\b )", r"\1\n\2", updated_text)
    return updated_text

# --- Display Output ---
edited_text = cit_claim(comm_text)

st.text_area(
    "Edited Claim 1 with Citations:",
    value=edited_text,
    height=400
)