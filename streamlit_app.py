import streamlit as st
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python_engine"))
from search_engine import load_model, build_index, semantic_search

st.set_page_config(page_title="Semantic Search", page_icon="🔍", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
* { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background: #0e1117; color: #e0e0e0; }
[data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #30363d; }
h1 { font-family: 'IBM Plex Mono', monospace !important; color: #58a6ff !important; font-size: 1.6rem !important; }
h3 { color: #8b949e !important; font-weight: 400 !important; font-size: 0.85rem !important; letter-spacing: 0.08em; text-transform: uppercase; }
.stTextArea textarea { background: #161b22 !important; color: #e0e0e0 !important; border: 1px solid #30363d !important; border-radius: 8px !important; font-size: 0.95rem !important; }
.stTextArea textarea:focus { border-color: #58a6ff !important; box-shadow: 0 0 0 2px rgba(88,166,255,0.15) !important; }
.stButton > button { background: #238636 !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 500 !important; padding: 0.5rem 1.5rem !important; font-size: 0.9rem !important; }
.stButton > button:hover { background: #2ea043 !important; }
.stFileUploader { border: 1px dashed #30363d !important; border-radius: 8px !important; padding: 0.5rem !important; }
.card { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 1.2rem 1.5rem; margin-bottom: 1rem; }
.card:hover { border-color: #58a6ff; }
.score { font-family: 'IBM Plex Mono', monospace; font-size: 1.3rem; font-weight: 600; color: #58a6ff; }
.filename { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #3fb950; background: rgba(63,185,80,0.1); padding: 0.2rem 0.6rem; border-radius: 4px; }
.chunk-text { font-size: 0.9rem; color: #8b949e; line-height: 1.7; margin-top: 0.75rem; border-left: 3px solid #30363d; padding-left: 0.75rem; }
.divider { border: none; border-top: 1px solid #21262d; margin: 1.5rem 0; }
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# Session state setup
if "index" not in st.session_state:
    st.session_state.index = []
if "model" not in st.session_state:
    st.session_state.model = None

@st.cache_resource
def get_model():
    return load_model()

# Sidebar
with st.sidebar:
    st.markdown("### 📁 Upload Documents")
    files = st.file_uploader(
        "PDF, TXT or DOCX",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if st.button("Index Documents", use_container_width=True):
        if files and len(files) > 3:
            st.warning("Please upload a maximum of 3 files for better performance.")
            st.stop()
        if not files:
            st.warning("Upload at least one file.")
        else:
            with st.spinner("Processing..."):
                model = get_model()
                st.session_state.model = model
                tmp = tempfile.mkdtemp()
                paths = []
                for f in files:
                    p = os.path.join(tmp, f.name)
                    open(p, "wb").write(f.getbuffer())
                    paths.append(p)
                st.session_state.index = build_index(paths, model)
            st.success(f"✓ Indexed {len(files)} file(s)")

    if st.session_state.index:
        st.markdown("---")
        st.markdown("### Indexed Files")
        names = list({item["filename"] for item in st.session_state.index})
        for n in names:
            st.markdown(f"- `{n}`")
        st.caption(f"{len(st.session_state.index)} total chunks")

    if st.session_state.index:
        if st.button("Clear", use_container_width=True):
            st.session_state.index = []
            st.rerun()

# Main page
st.markdown("# 🔍 Semantic Search")
st.markdown("### Navvya Chaudhary · BTech CSE (DSAI)")
st.markdown('<hr class="divider">', unsafe_allow_html=True)

if not st.session_state.index:
    st.info("👈 Upload documents from the sidebar and click **Index Documents** to get started.")
    st.markdown("""
    **How it works:**
    1. Upload your document (PDF, TXT, DOCX)
    2. Click Index Documents
    3. Ask any question about the content
    4. Get ranked results based on semantic similarity
    """)
else:
    top_n = st.slider("Results to show", 1, 8, 5)
    query = st.text_area("Ask a question about your documents", height=90,
                         placeholder="e.g. What are the main conclusions? / Explain the methodology used...")

    if st.button("Search", use_container_width=True):
        if not query.strip():
            st.warning("Please enter a question.")
        else:
            model = st.session_state.model or get_model()
            with st.spinner("Searching..."):
                results = semantic_search(query.strip(), st.session_state.index, model, top_n)

            st.markdown(f"**{len(results)} results** for: *{query}*")
            st.markdown('<hr class="divider">', unsafe_allow_html=True)

            for r in results:
                pct = r["score"] * 100
                st.markdown(f"""
                <div class="card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="filename">📄 {r['filename']}</span>
                        <span class="score">{pct:.1f}%</span>
                    </div>
                    <div class="chunk-text">{r['chunk_text']}</div>
                </div>
                """, unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.caption("Semantic Search · Navvya Chaudhary · BTech CSE (DSAI) · TF-IDF Vectorizer")
