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

# ---------- Custom CSS for colourful UI ----------
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
        font-size: 1.1rem;
        padding: 0.5rem 1.5rem;
    }
    .stTextInput input {
        background-color: rgba(255,255,255,0.9);
        color: black;
    }
    h1, h2, h3, p, div, span, label {
        color: white !important;
    }
    .response-box {
        background: rgba(0,0,0,0.5);
        border-radius: 20px;
        padding: 1rem;
        margin-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Session State ----------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# ---------- Title ----------
st.title("🎙️ AI English Teacher")
st.markdown("### Ask me anything – use **voice** or **text** – I will reply with **speech + text**.")

# ---------- API Key Input ----------
api_key = st.text_input(
    "🔑 Enter your Google Gemini API Key (free from https://aistudio.google.com)",
    type="password",
    value=st.session_state.api_key if st.session_state.api_key else ""
)
if api_key:
    st.session_state.api_key = api_key
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    st.success("✅ API Key accepted. You can now ask questions.")
else:
    st.warning("Please enter your Gemini API key to continue.")
    model = None

# ---------- Helper: Text-to-Speech (works on cloud) ----------
def speak_text(text):
    tts = gTTS(text=text, lang="en")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tts.save(f.name)
        with open(f.name, "rb") as audio_file:
            audio_bytes = audio_file.read()
        os.unlink(f.name)
    b64 = base64.b64encode(audio_bytes).decode()
    return f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}" controls style="width:100%; margin-top:0.5rem;"></audio>'

# ---------- Voice Input (mic recorder) ----------
if model:
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
        except sr.UnknownValueError:
            st.error("Sorry, could not understand the audio. Please speak clearly.")
            user_text = None
        except sr.RequestError as e:
            st.error(f"Speech recognition service error: {e}")
            user_text = None
        
        if user_text:
            # Store and get AI reply
            st.session_state.chat_history.append(("user", user_text))
            with st.spinner("🤖 Thinking..."):
                response = model.generate_content(user_text)
                ai_reply = response.text
            st.session_state.chat_history.append(("ai", ai_reply))
            
            # Display answer
            st.markdown(f"**You:** {user_text}")
            st.markdown(f"**AI Teacher:** {ai_reply}")
            # Play answer
            audio_html = speak_text(ai_reply)
            st.markdown(audio_html, unsafe_allow_html=True)

# ---------- Text Input ----------
st.markdown("---")
st.subheader("⌨️ Or type your question")
user_text_input = st.text_input("Type here...", key="text_q")
if st.button("Send (text)") and user_text_input and model:
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

if st.button("🗑️ Clear all history") and model:
    st.session_state.chat_history = []
    st.rerun()

# ---------- Footer ----------
st.markdown("---")
st.caption("Made with ❤️ by Gesner Deslandes – AI English Teacher")
