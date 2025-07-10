# 🧠 Patent Application Summary Tool

This is an interactive [Streamlit](https://streamlit.io/) web application that helps analyze patent applications by:

- Editing claims and general information
- Automatically extracting technical features from claims
- Visualizing the relationships between features in a network graph
- Generating summaries in Word format
- Syncing JSON data with Google Drive for backup and collaboration

---

## 🚀 Features

✅ Claim text editor  
✅ Automatic feature extraction using spaCy  
✅ Interactive Pyvis-based feature network graph  
✅ Marker and citation tools for claim refinement  
✅ Word document summary generation  
✅ Google Drive integration for loading and saving data

---
📂 Project Structure
.
├── app.py                     # Main entry point
├── pages/                     # Streamlit multipage tabs
│   ├── 1_General.py
│   ├── 2_Extract Features.py
│   ├── ...
├── utils.py                   # Google Drive sync helper functions
├── requirements.txt           # Python dependencies
├── .streamlit/
│   └── secrets.toml           # Local secrets (excluded from Git)
└── README.md


Built by Stefanos Stavroulis — [stavroulis@gmail.com]
