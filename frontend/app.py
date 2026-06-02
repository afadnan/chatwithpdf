import streamlit as st
import requests
import os

# Point to the backend container when in Docker, or localhost when developing locally
BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://localhost:8000")

st.set_page_config(page_title="Chat with PDF UI", page_icon="📄", layout="wide")
st.title("📄 Chat with PDF (Frontend UI)")
# Initialize session state variables to remember chat history and file status
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_ready" not in st.session_state:
    st.session_state.pdf_ready = False
# Sidebar for file uploading
with st.sidebar:
    st.header("1. Upload Document")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file and st.button("Process Document"):
        with st.spinner("Sending to backend engine..."):
            # Package the file as a multipart/form-data payload
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            try:
                # Send the file to the FastAPI backend
                res = requests.post(f"{BACKEND_API_URL}/api/v1/ingest", files=files)
                if res.status_code == 201:
                    st.success("PDF processed and indexed successfully!")
                    st.session_state.pdf_ready = True
                else:
                    st.error(f"Processing Error: {res.json().get('detail')}")
            except requests.exceptions.ConnectionError:
                st.error("Connection failed. Is the backend API running?")

# Main chat interface
st.header("2. Ask Questions")
if not st.session_state.pdf_ready:
    st.info("👈 Please upload and process a PDF in the sidebar first.")
else:
    # Render previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Handle new question
    if query_str := st.chat_input("Ask a question about your document..."):
        # Display user question
        st.session_state.messages.append({"role": "user", "content": query_str})
        with st.chat_message("user"):
            st.write(query_str)
        # Fetch and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Searching database and thinking..."):
                try:
                    payload = {"question": query_str}
                    res = requests.post(f"{BACKEND_API_URL}/api/v1/query", json=payload)

                    if res.status_code == 200:
                        answer = res.json()["answer"]
                        st.write(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        st.error("Backend encountered an error while searching.")
                except requests.exceptions.ConnectionError:
                    st.error("Connection failed. Is the backend API running?")