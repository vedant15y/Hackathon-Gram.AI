import streamlit as st
import requests
from speech_utils import transcribe_audio
from text_utils import text_to_speech
from PIL import Image
import tempfile

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide", page_title="Medical AI")

BACKEND_URL = "http://192.168.1.16:5000"   # 🔥 Flask server (Laptop B)

# ---------------- STATE ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "expanded"

if "image_panel" not in st.session_state:
    st.session_state.image_panel = False

if "images" not in st.session_state:
    st.session_state.images = []

# ---------------- SIDEBAR ----------------
def render_sidebar():
    with st.sidebar:
        st.title("🧠 Med AI")

        if st.button("☰ Toggle"):
            st.session_state.sidebar_state = (
                "collapsed"
                if st.session_state.sidebar_state == "expanded"
                else "expanded"
            )

        st.markdown("---")

        page = st.radio(
            "Navigation",
            ["🏠 Intro", "💬 Chat", "📊 Dashboard", "📁 History"],
            label_visibility="collapsed"
        )
        return page

# ---------------- INTRO PAGE ----------------
def intro_page():
    st.title("🧠 Multimodal Medical AI Assistant")
    st.markdown("### Analyze text, images, and voice inputs")

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    col1.info("💬 Text Analysis")
    col2.info("🖼️ Image Analysis")
    col3.info("🎤 Voice Input")

# ---------------- CHAT PAGE ----------------
def chat_page():
    st.title("💬 Medical Chat")

    # -------- CHAT DISPLAY --------
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # -------- INPUT --------
    user_input = st.chat_input("Type your medical query...")

    if user_input:
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        try:
            # 🔥 CALL FLASK BACKEND INSTEAD OF OLLAMA
            response = requests.post(
                f"{BACKEND_URL}/chat",
                json={
                    "message": user_input,
                    "user_id": None
                },
                timeout=15
            )

            data = response.json()
            reply = data.get("response", "No response")

        except Exception as e:
            reply = f"⚠️ Backend error: {str(e)}"

        # Add assistant message
        st.session_state.messages.append({
            "role": "assistant",
            "content": reply
        })

        st.rerun()

    # -------- IMAGE UPLOAD --------
    st.markdown("---")
    uploaded = st.file_uploader("Upload Image", type=["png", "jpg"])

    if uploaded:
        try:
            files = {"image": uploaded.getvalue()}

            response = requests.post(
                f"{BACKEND_URL}/image",
                files={"image": uploaded},
                timeout=30
            )

            reply = response.json().get("response", "No response")

            st.session_state.messages.append({
                "role": "assistant",
                "content": f"🖼️ Image Analysis:\n{reply}"
            })

            st.rerun()

        except Exception as e:
            st.error(f"Image upload failed: {e}")

    # -------- VOICE INPUT --------
    audio = st.file_uploader("Upload Voice", type=["wav"])

    if audio:
        try:
            files = {"audio": audio.getvalue()}

            response = requests.post(
                f"{BACKEND_URL}/voice",
                files={"audio": audio},
                timeout=30
            )

            data = response.json()

            st.session_state.messages.append({
                "role": "assistant",
                "content": data.get("response", "No response")
            })

            st.rerun()

        except Exception as e:
            st.error(f"Voice processing failed: {e}")

# ---------------- DASHBOARD ----------------
def dashboard_page():
    st.title("📊 Dashboard")

    col1, col2 = st.columns(2)
    col1.metric("Total Messages", len(st.session_state.messages))
    col2.metric("Images", len(st.session_state.images))

# ---------------- HISTORY ----------------
def history_page():
    st.title("📁 History")

    try:
        response = requests.post(
            f"{BACKEND_URL}/history",
            json={"user_id": None}
        )

        data = response.json()

        for msg in data.get("history", []):
            st.write(f"{msg['role']}: {msg['message']}")

    except:
        st.warning("Could not load history")

# ---------------- MAIN ----------------
page = render_sidebar()

if page == "🏠 Intro":
    intro_page()
elif page == "💬 Chat":
    chat_page()
elif page == "📊 Dashboard":
    dashboard_page()
elif page == "📁 History":
    history_page()