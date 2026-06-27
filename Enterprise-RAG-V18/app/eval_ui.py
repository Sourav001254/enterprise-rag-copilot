# app/eval_ui.py
import streamlit as st
import requests
import json
import sseclient

API_URL = "http://localhost:8000"
st.set_page_config(page_title="Evaluation Runner", layout="wide")

st.title("RAGAS Evaluation Runner")

# Dummy JWT for dev (Admin role)
DUMMY_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
headers = {"Authorization": f"Bearer {DUMMY_TOKEN}"}

if st.button("Run Evaluation on Golden Dataset"):
    st.info("Triggering evaluation...")
    
    # Normally this would call the API. We'll simulate SSE progress since 
    # eval takes a long time.
    try:
        response = requests.post(f"{API_URL}/eval/run", headers=headers, stream=True)
        if response.status_code == 200:
            client = sseclient.SSEClient(response)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for event in client.events():
                if event.data == "[DONE]":
                    break
                    
                data = json.loads(event.data)
                if "progress" in data:
                    progress_bar.progress(data["progress"])
                if "message" in data:
                    status_text.text(data["message"])
                if "results" in data:
                    st.success("Evaluation Complete!")
                    st.json(data["results"])
        else:
            st.error(f"Failed to start evaluation: {response.text}")
    except Exception as e:
        st.error(f"Connection failed: {e}")
