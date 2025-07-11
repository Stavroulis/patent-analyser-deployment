import streamlit as st
import networkx as nx
import pandas as pd
from pathlib import Path
from itertools import cycle
from pyvis.network import Network
import tempfile
import json
from utils import secure_filename

# Color cycle for claims
COLORS = ["red", "orange", "lime", "turquoise", "hotpink", "khaki", "blue",
          "green", "yellow", "violet", "coral", "pink", "steelblue",
          "salmon", "tomato", "springgreen"] * 10

# --- Session Checks ---
if "filename" not in st.session_state:
    st.warning("No file selected. Please go to the main page.")
    st.stop()

filename = secure_filename(st.session_state["filename"])  # ✅ sanitize
data = st.session_state.get("summary_data", {})
json_path = Path(f"data/{filename}/Summary_{filename}.json")
Path(f"data/{filename}").mkdir(parents=True, exist_ok=True)

st.title(f"Network Graph for {filename}")

# --- Save Utility ---
def save_to_local():
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Utility Functions ---
def concatatened_dataframe(df_data):
    rows = []
    a_list = df_data.get('a_list', [])
    prep_list = df_data.get('prep_list', [])
    the_list = df_data.get('the_list', [])
    cl_nr_list = df_data.get('Cl_nr', [])
    max_len = max(len(a_list), len(prep_list), len(the_list), len(cl_nr_list))

    a_list += [''] * (max_len - len(a_list))
    prep_list += [''] * (max_len - len(prep_list))
    the_list += [''] * (max_len - len(the_list))
    cl_nr_list += [''] * (max_len - len(cl_nr_list))

    for i in range(max_len):
        rows.append([i, a_list[i], prep_list[i], the_list[i], cl_nr_list[i]])

    df = pd.DataFrame(rows, columns=['index', 'a_list', 'prep_list', 'the_list', 'Cl_nr'])
    return df

def create_graph(df):
    G = nx.DiGraph()
    color_cycle = cycle(COLORS)
    node_colors = {}
    claim_colors = {}

    for _, row in df.iterrows():
        node = row['a_list']
        claim = row['Cl_nr']
        if pd.notna(node) and node.strip():
            if node not in node_colors:
                if claim not in claim_colors:
                    claim_colors[claim] = next(color_cycle)
                node_colors[node] = claim_colors[claim]

    for node, color in node_colors.items():
        G.add_node(node, color=color)

    for i in range(len(df) - 2):
        node_a, node_b = None, None
        edge_label = df.at[i + 1, 'prep_list'] if pd.notna(df.at[i + 1, 'prep_list']) else ""

        if pd.notna(df.at[i, 'a_list']) and df.at[i, 'a_list'].strip():
            if pd.isna(df.at[i + 2, 'the_list']) or not df.at[i + 2, 'the_list'].strip():
                if pd.notna(df.at[i + 2, 'a_list']) and df.at[i + 2, 'a_list'].strip():
                    node_a = df.at[i, 'a_list']
                    node_b = df.at[i + 2, 'a_list']
        elif pd.notna(df.at[i, 'the_list']) and df.at[i, 'the_list'].strip():
            if pd.notna(df.at[i + 2, 'a_list']) and df.at[i + 2, 'a_list'].strip():
                node_a = next((n for n in df['a_list'] if n == df.at[i, 'the_list']), None)
                node_b = df.at[i + 2, 'a_list']

        if node_a and node_b:
            G.add_edge(node_a, node_b, label=edge_label)

    nx.set_node_attributes(G, {node: 0 for node in G.nodes}, "subset")
    return G

def display_pyvis_graph(G):
    net = Network(notebook=False)
    for node, attrs in G.nodes(data=True):
        net.add_node(str(node), label=str(node), color=attrs.get("color", "lightblue"))
    for edge in G.edges(data=True):
        net.add_edge(str(edge[0]), str(edge[1]), title=edge[2].get("label", ""))
    return net

def display_color_legend(num_claims):
    st.subheader("Claim Color Legend")
    for i in range(num_claims):
        st.markdown(
            f'<span style="color: {COLORS[i]}; font-weight: bold;">■ Claim {i+1}</span>',
            unsafe_allow_html=True
        )

# --- Main Graph Build ---
network_features = data.get("Concatenated DataFrame", {})

if not network_features or not any(network_features.values()):
    st.warning("⚠️ No network data found. Please extract features first in '2_Extract Features' and save them.")
    st.stop()

df = concatatened_dataframe(network_features)
display_color_legend(len(set(df["Cl_nr"])))

G = create_graph(df)
st.session_state["G"] = G

net = display_pyvis_graph(G)
with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html", encoding="utf-8") as tmp_file:
    net.save_graph(tmp_file.name)
    with open(tmp_file.name, encoding="utf-8") as f:
        html_content = f.read()

st.components.v1.html(html_content, height=500)

# --- Graph Controls ---
st.subheader("Modify Graph")

col1, col2 = st.columns([3, 1])
with col1:
    with st.form("add_node_form"):
        new_node = st.text_input("Node Name")
        add_node_submit = st.form_submit_button("Add Node")
with col2:
    with st.form("del_node_form"):
        node_to_delete = st.selectbox("Delete Node", list(G.nodes), key="del_node")
        del_node_submit = st.form_submit_button("Del Node")

if add_node_submit and new_node:
    if new_node not in G.nodes:
        G.add_node(new_node, color="yellow")
        st.session_state["G"] = G
        st.rerun()

if del_node_submit and node_to_delete:
    G.remove_node(node_to_delete)
    st.session_state["G"] = G
    st.rerun()

col3, col4 = st.columns([3, 1])
with col3:
    with st.form("add_edge_form"):
        node_options = list(G.nodes)
        edge_node1 = st.selectbox("From", node_options, key="edge1")
        edge_node2 = st.selectbox("To", node_options, key="edge2")
        edge_label = st.text_input("Edge Label (optional)")
        add_edge_submit = st.form_submit_button("Add Edge")
with col4:
    with st.form("del_edge_form"):
        edge_options = [f"{u} -> {v}" for u, v in G.edges]
        edge_to_delete = st.selectbox("Delete Edge", edge_options, key="del_edge")
        del_edge_submit = st.form_submit_button("Del Edge")

if add_edge_submit and edge_node1 and edge_node2:
    G.add_edge(edge_node1, edge_node2, label=edge_label)
    st.session_state["G"] = G
    st.rerun()

if del_edge_submit and edge_to_delete:
    u, v = edge_to_delete.split(" -> ")
    G.remove_edge(u, v)
    st.session_state["G"] = G
    st.rerun()

# --- Final Save Button ---
if st.button("💾 Save Graph Locally", type="primary", use_container_width=True):
    network_data = {
        "nodes": [{"id": node, "color": G.nodes[node].get("color", "lightblue")} for node in G.nodes],
        "edges": [{"source": u, "target": v, "label": G.edges[u, v].get("label", "")} for u, v in G.edges]
    }
    data["Network"] = network_data
    st.session_state["summary_data"] = data
    save_to_local()
    st.success(f"✅ Graph saved locally to {json_path}")
