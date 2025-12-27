import streamlit as st
import requests
import json

# ================= CONFIG =================
API_BASE = "http://localhost:8000"  # change if needed
st.set_page_config(
    page_title="Document Portal",
    layout="wide",
)

# ================= THEME =================
st.markdown("""
<style>
body { font-family: Inter, sans-serif; }
.block-container { padding-top: 1.5rem; }
h1, h2, h3 { font-weight: 600; }
pre { background:#0a0f16; color:#e8f0ff; padding:1rem; border-radius:12px; }
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.title("📚 Document Portal")

tab_analysis, tab_compare, tab_chat = st.tabs(
    ["🔎 Document Analysis", "🆚 Document Compare", "💬 Doc Chat"]
)

# ============================================================
# 🔎 DOCUMENT ANALYSIS
# ============================================================
with tab_analysis:
    st.subheader("Analyze a Document")
    st.caption("Upload a PDF and get structured metadata analysis.")

    file = st.file_uploader("Upload PDF", type=["pdf"])

    if st.button("Run Analysis", use_container_width=True):
        if not file:
            st.warning("Please upload a PDF.")
        else:
            with st.spinner("Running analysis..."):
                try:
                    files = {"file": (file.name, file, "application/pdf")}
                    res = requests.post(f"{API_BASE}/analyze", files=files)

                    if res.status_code != 200:
                        st.error(res.text)
                    else:
                        st.success("Analysis complete")
                        st.json(res.json())
                except Exception as e:
                    st.error(str(e))

# ============================================================
# 🆚 DOCUMENT COMPARE
# ============================================================
with tab_compare:
    st.subheader("Compare Two Documents")
    st.caption("Upload a reference PDF and an actual PDF to compare page-wise changes.")

    col1, col2 = st.columns(2)
    with col1:
        ref = st.file_uploader("Reference PDF", type=["pdf"], key="ref")
    with col2:
        act = st.file_uploader("Actual PDF", type=["pdf"], key="act")

    if st.button("Compare", use_container_width=True):
        if not ref or not act:
            st.warning("Upload both PDFs.")
        else:
            with st.spinner("Comparing documents..."):
                try:
                    files = {
                        "reference": (ref.name, ref, "application/pdf"),
                        "actual": (act.name, act, "application/pdf"),
                    }
                    res = requests.post(f"{API_BASE}/compare", files=files)

                    if res.status_code != 200:
                        st.error(res.text)
                    else:
                        rows = res.json().get("rows", [])
                        if not rows:
                            st.info("No differences found.")
                        else:
                            st.dataframe(rows, use_container_width=True)
                except Exception as e:
                    st.error(str(e))

# ============================================================
# 💬 DOCUMENT CHAT (RAG)
# ============================================================
with tab_chat:
    st.subheader("Chat with your Documents")
    st.caption("Upload files → FAISS index → RAG Q&A")

    # ---------- INDEX ----------
    with st.expander("📦 Build / Update Index", expanded=True):
        files = st.file_uploader(
            "Upload files",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            session_id = st.text_input("Session ID (optional)")
        with col2:
            chunk_size = st.number_input("Chunk size", 200, 2000, 1000, 100)
        with col3:
            chunk_overlap = st.number_input("Chunk overlap", 0, 500, 200, 50)

        col4, col5 = st.columns(2)
        with col4:
            top_k = st.number_input("Top-K", 1, 20, 5)
        with col5:
            use_session = st.checkbox("Use session-based FAISS", value=True)

        if st.button("Build / Update Index", use_container_width=True):
            if not files:
                st.warning("Upload at least one file.")
            else:
                with st.spinner("Building index..."):
                    try:
                        fd = []
                        for f in files:
                            fd.append(("files", (f.name, f, "application/octet-stream")))

                        data = {
                            "session_id": session_id,
                            "chunk_size": chunk_size,
                            "chunk_overlap": chunk_overlap,
                            "k": top_k,
                            "use_session_dirs": str(use_session).lower()
                        }

                        res = requests.post(
                            f"{API_BASE}/chat/index",
                            files=fd,
                            data=data
                        )

                        if res.status_code != 200:
                            st.error(res.text)
                        else:
                            out = res.json()
                            st.session_state["session"] = out.get("session_id")
                            st.success(f"Indexed ✔ Session: {st.session_state['session']}")
                    except Exception as e:
                        st.error(str(e))

    # ---------- QUERY ----------
    st.divider()
    question = st.text_input("Ask a question")

    if st.button("Send", use_container_width=True):
        if not question:
            st.warning("Enter a question.")
        elif use_session and "session" not in st.session_state:
            st.warning("Build index first.")
        else:
            with st.spinner("Thinking..."):
                try:
                    data = {
                        "question": question,
                        "k": top_k,
                        "use_session_dirs": str(use_session).lower()
                    }
                    if use_session:
                        data["session_id"] = st.session_state["session"]

                    res = requests.post(
                        f"{API_BASE}/chat/query",
                        data=data
                    )

                    if res.status_code != 200:
                        st.error(res.text)
                    else:
                        answer = res.json().get("answer")
                        st.markdown("### Answer")
                        st.markdown(answer or "No answer.")
                except Exception as e:
                    st.error(str(e))
