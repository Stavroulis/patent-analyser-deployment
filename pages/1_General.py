import streamlit as st
from pathlib import Path
from PIL import Image
from datetime import datetime
import json
from utils import secure_filename 

# Configure Streamlit
st.set_page_config(layout="wide")

# Ensure filename is in session state
if "filename" not in st.session_state:
    st.warning("No file selected. Please go to the main page.")
    st.stop()

filename = secure_filename(st.session_state["filename"])  # ✅ sanitize
data = st.session_state.get("summary_data", {})

st.title(f"General Information for {filename}")

# Define paths
directory = Path(f"data/{filename}")
directory.mkdir(parents=True, exist_ok=True)
json_path = directory / f"Summary_{filename}.json"
image_path = directory / f"appl_image_{filename}.png"

# Define input placeholders
PLACEHOLDERS = {
    "Independent Claims": "Claim 1 discloses ...",
    "Ptbs": "How to improve, prevent, enable...",
    "Technical Effect": "Reduce non-linearity, increase sensitivity/accuracy, reduce effort...",
    "Solution": "By...",
    "Keywords": "Enter relevant keywords...",
    "Classes": "Enter classification info...",
    "Unity": "Describe unity...",
    "Remarks": "Consulted: ...",
    "Prior Art": "Enter prior art information..."
}

# Layout
col_general, col_claims, col_image = st.columns([0.3, 0.3, 0.3])

with col_general:
    st.subheader("General")
    for key, placeholder in PLACEHOLDERS.items():
        data[key] = st.text_area(
            key,
            value=data.get(key, ""),
            key=f"input_{key}",
            placeholder=placeholder
        )

with col_claims:
    st.subheader("Claims")
    data["Nr. Claims"] = st.text_input(
        "Number of claims",
        value=data.get("Nr. Claims", ""),
        key="nr_claims",
        placeholder="Enter number of claims..."
    )

with col_image:
    st.subheader("Appl. Image")
    uploaded_image = st.file_uploader("Upload an Image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        with open(image_path, "wb") as img_file:
            img_file.write(uploaded_image.getbuffer())
        data["Appl. Image"] = str(image_path)
        st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)
    elif data.get("Appl. Image"):
        try:
            image = Image.open(data["Appl. Image"])
            st.image(image, caption="Application Image", use_container_width=True)
        except Exception as e:
            st.error(f"Error loading image: {e}")

# --- Save Button ---
def save_to_local():
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

if st.button("💾 Save Locally", type="primary", use_container_width=True):
    data["Date"] = datetime.now().strftime("%d-%m-%Y")
    st.session_state["summary_data"] = data
    save_to_local()
    st.success(f"Data saved locally to {json_path}")
