import streamlit as st
import networkx as nx
from pathlib import Path
import spacy
import json
from utils import secure_filename 

# --- Caching the spaCy model ---
@st.cache_resource
def get_nlp():
    return spacy.load("en_core_web_sm")

nlp = get_nlp()

# --- Session Checks ---
if "filename" not in st.session_state:
    st.warning("No file selected. Please go to the main page.")
    st.stop()

filename = secure_filename(st.session_state["filename"])  # ✅ sanitize
data = st.session_state.get("summary_data", {})
json_path = Path(f"data/{filename}/Summary_{filename}.json")
Path(f"data/{filename}").mkdir(parents=True, exist_ok=True)

st.title(f"Concept Markers for {filename}")

# --- Save Utility ---
def save_to_local():
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Graph Reconstruction ---
def create_graph_from_network_data(network_data):
    G = nx.DiGraph()
    for node in network_data.get('nodes', []):
        G.add_node(node['id'], color=node['color'])
    for edge in network_data.get('edges', []):
        G.add_edge(edge['source'], edge['target'], label=edge.get('label', ''))
    return G

def find_head_nodes(G):
    return [node for node in G.nodes if G.in_degree(node) == 0]

def find_all_branches(G, start_node):
    branches = []
    def dfs(path):
        node = path[-1]
        for neighbor in G.neighbors(node):
            if neighbor not in path:
                dfs(path + [neighbor])
        if len(path) > 1:
            branches.append(path)
    dfs([start_node])
    return branches

def generate_markers_dict(network_data, G):
    head_nodes = find_head_nodes(G)
    all_branches = {head: find_all_branches(G, head) for head in head_nodes}
    combinations = [node['id'] for node in network_data.get("nodes", [])]
    branches_info = {
        head: [
            f"10UG ({', '.join(branch)})"
            for branch in branches if len(branch) > 1
        ]
        for head, branches in all_branches.items()
        if any(len(branch) > 1 for branch in branches)
    }
    return {
        "Combinations": combinations,
        "Heads": head_nodes,
        "Branches": branches_info
    }

def format_markers_for_display(markers_dict):
    text = ""
    for key, value in markers_dict.items():
        text += f"{key}\n\n"
        if isinstance(value, list):
            text += "\n".join(value) + "\n"
        elif isinstance(value, dict):
            for head, branches in value.items():
                text += f"{head}:\n"
                text += "\n".join(branches) + "\n"
        text += "\n---   ---   ---   --- \n\n"
    return text.strip()

# --- Logic Execution ---
network_data = data.get("Network", {})
if not network_data:
    st.warning("⚠️ No saved network found. Please build and save a graph in '3_Network Pyvis' first.")
    st.stop()

G = create_graph_from_network_data(network_data)
markers_dict = generate_markers_dict(network_data, G)

formatted_text = format_markers_for_display(markers_dict)
concepts_text = st.text_area(
    label="Concepts",
    value=formatted_text,
    height=500,
    key="concepts_text"
)

# --- Save ---
if st.button("💾 Save Markers Locally", type="primary", use_container_width=True):
    data["Markers"] = markers_dict
    st.session_state["summary_data"] = data
    save_to_local()
    st.success(f"✅ Markers saved locally to {json_path}")
