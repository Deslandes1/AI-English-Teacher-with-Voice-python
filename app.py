import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import base64
import tempfile
import os
import io
import speech_recognition as sr
from streamlit_mic_recorder import mic_recorder

st.set_page_config(
    page_title="AI English Teacher – Gesner Deslandes",
    page_icon="🎙️",
    layout="centered"
)

# ---------- Custom CSS ----------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb4d);
    }
    .stButton button {
        background-color: #ff9a3c !important;
        color: white !important;
        border-radius: 50px !important;
        font-weight: bold;
    }
    h1, h2, h3, p, div, span, label {
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- HARDCODED API KEY (REPLACE WITH YOUR NEW KEY) ----------
# 🔐 IMPORTANT: Create a NEW key from https://aistudio.google.com/app/apikey
# Then paste it below (between the quotes). Do NOT use the leaked key.
API_KEY = "YOUR_NEW_API_KEY_HERE"   # <---- PASTE YOUR NEW KEY HERE

if API_KEY == "YOUR_NEW_API_KEY_HERE":
    st.error("❌ Please replace 'YOUR_NEW_API_KEY_HERE' with your actual Gemini API key.")
    st.stop()

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ---------- Session State ----------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------- Title ----------
st.title("🎙️ AI English Teacher")
st.markdown("### Ask anything – **voice** or **text** – I’ll reply with **speech + text**.")

# ---------- Text-to-Speech ----------
def speak_text(text):
    tts = gTTS(text=text, lang="en")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tts.save(f.name)
        with open(f.name, "rb") as audio_file:
            audio_bytes = audio_file.read()
        os.unlink(f.name)
    b64 = base64.b64encode(audio_bytes).decode()
    return f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}" controls style="width:100%; margin-top:0.5rem;"></audio>'

# ---------- Voice Input ----------
st.markdown("---")
st.subheader("🎤 Speak your question")
audio = mic_recorder(
    start_prompt="🔴 Start recording",
    stop_prompt="⏹️ Stop",
    key="mic",
    format="wav"
)

if audio:
    st.audio(audio['bytes'], format="audio/wav")
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(audio['bytes'])) as source:
            recorded = recognizer.record(source)
            user_text = recognizer.recognize_google(recorded)
        st.success(f"📝 Transcribed: \"{user_text}\"")
    except Exception as e:
        st.error(f"Speech recognition error: {e}")
        user_text = None

    if user_text:
        st.session_state.chat_history.append(("user", user_text))
        with st.spinner("🤖 Thinking..."):
            response = model.generate_content(user_text)
            ai_reply = response.text
        st.session_state.chat_history.append(("ai", ai_reply))

        st.markdown(f"**You:** {user_text}")
        st.markdown(f"**AI Teacher:** {ai_reply}")
        audio_html = speak_text(ai_reply)
        st.markdown(audio_html, unsafe_allow_html=True)

# ---------- Text Input ----------
st.markdown("---")
st.subheader("⌨️ Or type your question")
user_text_input = st.text_input("Type here...", key="text_q")
if st.button("Send (text)") and user_text_input:
    st.session_state.chat_history.append(("user", user_text_input))
    with st.spinner("🤖 Thinking..."):
        response = model.generate_content(user_text_input)
        ai_reply = response.text
    st.session_state.chat_history.append(("ai", ai_reply))

    st.markdown(f"**You:** {user_text_input}")
    st.markdown(f"**AI Teacher:** {ai_reply}")
    audio_html = speak_text(ai_reply)
    st.markdown(audio_html, unsafe_allow_html=True)

# ---------- Chat History ----------
st.markdown("---")
st.subheader("📝 Conversation History")
for role, msg in st.session_state.chat_history:
    if role == "user":
        st.markdown(f"**🧑‍🎓 You:** {msg}")
    else:
        st.markdown(f"**🤖 AI Teacher:** {msg}")

if st.button("🗑️ Clear all history"):
    st.session_state.chat_history = []
    st.rerun()

st.markdown("---")
st.caption("Made with ❤️ by Gesner Deslandes – AI English Teacher")
