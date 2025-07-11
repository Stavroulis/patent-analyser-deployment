import streamlit as st
import re
import spacy
import pandas as pd
from pathlib import Path
import json
from utils import secure_filename 

# --- Caching NLP model ---
@st.cache_resource
def get_nlp():
    return spacy.load("en_core_web_sm")

nlp = get_nlp()

# --- Session/filename checks ---
if "filename" not in st.session_state:
    st.warning("No file selected. Please go to the main page.")
    st.stop()

filename = secure_filename(st.session_state["filename"])  # ✅ sanitize
data = st.session_state.get("summary_data", {})
json_path = Path(f"data/{filename}/Summary_{filename}.json")
Path(f"data/{filename}").mkdir(parents=True, exist_ok=True)
st.title(f"Automatic Features Extraction for {filename}")

# --- Claims text area ---
initial_claims_text = "\n".join(data.get("User Entered Claims", {}).values())
claims_text = st.text_area(
    label="Claims Text",
    value=initial_claims_text if initial_claims_text else "",
    height=300,
    key="claims_text",
    placeholder="Enter your claims here and click outside the box ..."
)

# --- Utility functions ---
def remove_parenthesized_text(claim):
    cleaned = re.sub(r'\([^)]*\)', '', claim)
    return re.sub(r'\s+', ' ', cleaned).strip()

def extract_noun_chunks(claim):
    doc = nlp(claim)
    chunks = []
    for chunk in doc.noun_chunks:
        words = chunk.text.split()
        if doc[chunk.start].pos_ == "DET" and doc[chunk.start].text.lower() not in {"a", "an", "the"}:
            words = words[1:]
        for i, word in enumerate(words):
            if word.lower() in {"for", "with", "by", "of", "on", "at"}:
                words = words[:i]
                break
        noun_phrase = " ".join(words).strip()
        if noun_phrase and len(noun_phrase.split()) > 1:
            chunks.append(noun_phrase)

    words = claim.split()
    for i in range(len(words) - 1):
        if words[i].lower() in {"a", "an", "the"} and words[i+1].isalpha():
            chunks.insert(0, f"{words[i]} {words[i+1]}")
            break
    return chunks

def apply_highlighting(claim, chunks):
    highlighted = claim
    for chunk in chunks:
        highlighted = re.sub(rf'\b{re.escape(chunk)}\b', f'<b style="color:red;">{chunk}</b>', highlighted)
    return highlighted

def create_feature_table(features, num_claims):
    filtered = {
        k: [term for term in v if not term.lower().startswith(("the ", "said "))]
        for k, v in features.items()
    }
    df = pd.DataFrame.from_dict(filtered, orient="index").T
    df.columns = [f"Cl_{i+1}" for i in range(num_claims)]
    df.index = [f"Feature {i+1}" for i in range(df.shape[0])]
    st.markdown(df.to_html(escape=False), unsafe_allow_html=True)
    return df

def save_to_local():
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Main logic ---
if claims_text:
    claims_list = [claim.strip() for claim in claims_text.split("\n") if claim.strip()]
    cleaned_claims = [remove_parenthesized_text(claim) for claim in claims_list]

    extracted_features = {i: extract_noun_chunks(claim) for i, claim in enumerate(cleaned_claims)}

    highlighted_claims = [
        apply_highlighting(claim, extracted_features[i])
        for i, claim in enumerate(cleaned_claims)
    ]
    formatted = "".join(f'<div style="margin-bottom: 10px;">{c}</div>' for c in highlighted_claims)

    st.subheader("Automatically Highlighted Claims")
    st.markdown(formatted, unsafe_allow_html=True)

    st.subheader("Feature Table")
    feature_df = create_feature_table(extracted_features, len(cleaned_claims))
    edited_feature_df = st.data_editor(feature_df, num_rows="dynamic")

    if st.button("💾 Save Locally", type="primary", use_container_width=True):
        data["User Entered Claims"] = {f"Cl_{i+1}": claim for i, claim in enumerate(cleaned_claims)}
        data["Feature Table"] = {f"Cl_{i+1}": extracted_features.get(i, []) for i in range(len(cleaned_claims))}
        data["Edited Feature Table"] = {
            f"Cl_{i+1}": edited_feature_df.iloc[:, i].dropna().tolist()
            for i in range(edited_feature_df.shape[1])
        }

        # Build data for network graph
        flat_data = {
            "a_list": [],
            "prep_list": [],
            "the_list": [],
            "Cl_nr": []
        }

        for col in edited_feature_df.columns:
            claim_label = col
            for val in edited_feature_df[col].dropna():
                flat_data["a_list"].append(val)
                flat_data["prep_list"].append("")   # editable later
                flat_data["the_list"].append("")    # optional
                flat_data["Cl_nr"].append(claim_label)

        data["Concatenated DataFrame"] = flat_data

        # Save all to disk
        st.session_state["summary_data"] = data
        save_to_local()
        st.success(f"✅ Data saved locally to {json_path}")
