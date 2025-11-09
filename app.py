import os
import time
import random
import requests
import streamlit as st

# ----------------------------
# CONFIG
# ----------------------------
API_URL = "https://ark.ap-southeast.bytepluses.com/api/v3/chat/completions"
#https://ark.ap-southeast.bytepluses.com/api/v3/responses
API_KEY = os.environ.get("ARK_API_KEY") or st.secrets.get("ARK_API_KEY")
MODEL = "seed-translation-250915"
SOURCE_LANG = "en"
TARGET_LANG = "vi"
TEXT_SAMPLE = "This is a test paragraph to be translated repeatedly by Seed Translation."

# ----------------------------
# HELPER FUNCTION
# ----------------------------
def call_translation_api():
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": f"Translate from {SOURCE_LANG} to {TARGET_LANG}."},
            {"role": "user", "content": TEXT_SAMPLE}
        ]
    }
    try:
        resp = requests.post(API_URL, json=payload, headers=headers)
        data = resp.json()
        tokens = data.get("usage", {}).get("total_tokens", 0)
        st.session_state.total_tokens += tokens
        st.session_state.logs.append(f"[{time.ctime()}] +{tokens} tokens → Total: {st.session_state.total_tokens}")
    except Exception as e:
        st.session_state.logs.append(f"[{time.ctime()}] ❌ Error: {e}")

# ----------------------------
# STREAMLIT UI
# ----------------------------
st.set_page_config(page_title="Seed Translation Runner", layout="wide")

if "running" not in st.session_state:
    st.session_state.running = False
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0
if "logs" not in st.session_state:
    st.session_state.logs = []

st.title("🌏 Seed Translation Auto Runner")
st.caption("Automatically call ByteDance Seed Translation API and track token usage live.")

col1, col2, col3 = st.columns(3)
with col1:
    start_button = st.button("▶️ Start Auto Run")
with col2:
    stop_button = st.button("⏹️ Stop")
with col3:
    reset_button = st.button("🔄 Reset Counter")

if start_button:
    st.session_state.running = True
if stop_button:
    st.session_state.running = False
if reset_button:
    st.session_state.total_tokens = 0
    st.session_state.logs = []

if st.session_state.running:
    st.success("Running...")
    with st.spinner("Calling Seed Translation API repeatedly..."):
        for _ in range(20):  # Each click runs 20 loops (~few minutes)
            if not st.session_state.running:
                break
            call_translation_api()
            st.experimental_rerun()
            time.sleep(random.uniform(1, 3))

st.metric("💬 Total Tokens Consumed", st.session_state.total_tokens)
st.text_area("📜 Logs", "\n".join(st.session_state.logs), height=300)
