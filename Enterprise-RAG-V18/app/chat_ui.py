# app/chat_ui.py
import streamlit as st
import requests
import json
import sseclient
import uuid

API_URL = "http://localhost:8000"
st.set_page_config(page_title="SRE Copilot", page_icon="☸️", layout="wide")

st.title("Enterprise Advanced RAG — Kubernetes SRE Copilot")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    
if "messages" not in st.session_state:
    st.session_state.messages = []
    
import os

# JWT for dev/prod. Should be injected via env.
AUTH_TOKEN = os.getenv("DEV_AUTH_TOKEN", "")
if not AUTH_TOKEN:
    st.warning("DEV_AUTH_TOKEN is not set in the environment. Authentication may fail.")

headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}

# Sidebar settings
with st.sidebar:
    st.header("Settings")
    stream_mode = st.toggle("Enable Streaming", value=True)
    st.write(f"Session ID: {st.session_state.session_id}")
    if st.button("Clear History"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("Sources"):
                for s in msg["sources"]:
                    st.write(f"[{s['score']:.2f}] {s['url']}")

if prompt := st.chat_input("Ask a Kubernetes question..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status_placeholder = st.empty()
        
        payload = {"query": prompt, "session_id": st.session_state.session_id}
        
        if stream_mode:
            # Feature I: SSE Streaming
            try:
                response = requests.post(f"{API_URL}/query/stream", json=payload, headers=headers, stream=True)
                client = sseclient.SSEClient(response)
                
                full_answer = ""
                for event in client.events():
                    if event.data == "[DONE]":
                        break
                    
                    data = json.loads(event.data)
                    if "error" in data:
                        full_answer = f"Error: {data['error']}"
                        break
                        
                    stage = data.get("stage")
                    status = data.get("status")
                    
                    if status == "started":
                        status_placeholder.info(f"Running: {stage}...")
                    elif status == "complete":
                        status_placeholder.success(f"Completed: {stage}")
                    elif status == "streaming":
                        token = data.get("token", "")
                        full_answer += token
                        message_placeholder.markdown(full_answer + "▌")
                        
                message_placeholder.markdown(full_answer)
                status_placeholder.empty()
                st.session_state.messages.append({"role": "assistant", "content": full_answer})
                
            except Exception as e:
                st.error(f"Streaming failed: {e}")
        else:
            with st.spinner("Thinking..."):
                response = requests.post(f"{API_URL}/query", json=payload, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    sources = data.get("sources", [])
                    
                    if data.get("degraded"):
                        st.warning("Running in degraded mode.")
                        
                    message_placeholder.markdown(answer)
                    
                    if sources:
                        with st.expander("Sources"):
                            for s in sources:
                                st.write(f"[{s['score']:.2f}] {s['url']}")
                                
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer,
                        "sources": sources
                    })
                else:
                    st.error(f"Error: {response.text}")
