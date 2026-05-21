import streamlit as st
import speech_recognition as sr
import pyttsx3
import os
import tempfile
import base64
from gtts import gTTS
import google.generativeai as genai

# ---------- Page config ----------
st.set_page_config(
    page_title="AI English Teacher – Gesner Deslandes",
    page_icon="🎙️",
    layout="centered"
)

# ---------- Custom CSS for nice UI ----------
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
        font-size: 1.2rem;
        padding: 0.5rem 2rem;
    }
    h1, h2, p, div, span {
        color: white !important;
    }
    .response-box {
        background: rgba(0,0,0,0.6);
        border-radius: 20px;
        padding: 1rem;
        margin-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Session state ----------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------- AI Setup (Gemini) ----------
# Get your free API key from https://aistudio.google.com/app/apikey
# For security, use st.secrets or environment variable. Here we'll ask user to input.
API_KEY = st.text_input("🔑 Enter your Google Gemini API Key", type="password")
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.warning("Please enter your Gemini API key to enable AI answers. Get one free at https://aistudio.google.com/app/apikey")
    model = None

# ---------- Text-to-Speech function ----------
def speak_text(text):
    """Convert text to speech and play it in browser."""
    tts = gTTS(text=text, lang='en', slow=False)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
        tts.save(tmpfile.name)
        audio_file = open(tmpfile.name, 'rb')
        audio_bytes = audio_file.read()
        audio_file.close()
        os.unlink(tmpfile.name)  # clean up
        return base64.b64encode(audio_bytes).decode()

# ---------- Speech Recognition ----------
def listen_microphone():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening... Speak now")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            st.success("✅ Captured! Processing...")
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            st.error("Sorry, I could not understand that. Please try again.")
            return None
        except sr.RequestError as e:
            st.error(f"Speech recognition service error: {e}")
            return None
        except sr.WaitTimeoutError:
            st.error("No speech detected. Please speak louder or check your microphone.")
            return None

# ---------- Main UI ----------
st.title("🎙️ AI English Teacher")
st.markdown("Ask me anything in English – I will answer with **text and voice**.")

# Voice input button
if st.button("🎤 Click and Speak Your Question"):
    user_text = listen_microphone()
    if user_text and model:
        # Store user message
        st.session_state.chat_history.append(("user", user_text))
        
        # Get AI response
        with st.spinner("🤖 Thinking..."):
            response = model.generate_content(user_text)
            ai_reply = response.text
        
        # Store AI reply
        st.session_state.chat_history.append(("ai", ai_reply))
        
        # Display conversation
        st.markdown("---")
        for role, msg in st.session_state.chat_history:
            if role == "user":
                st.markdown(f"**You:** {msg}")
            else:
                st.markdown(f"**AI Teacher:** {msg}")
        
        # Convert AI reply to speech and play
        audio_b64 = speak_text(ai_reply)
        audio_html = f'<audio autoplay="true" src="data:audio/mp3;base64,{audio_b64}" controls></audio>'
        st.markdown(audio_html, unsafe_allow_html=True)
        
    elif user_text and not model:
        st.error("Please enter a valid Gemini API key first.")

# Manual text input (alternative)
st.markdown("---")
st.markdown("Or type your question below:")
user_text_input = st.text_input("Type here...")
if st.button("Send Text Question") and user_text_input and model:
    st.session_state.chat_history.append(("user", user_text_input))
    with st.spinner("🤖 Thinking..."):
        response = model.generate_content(user_text_input)
        ai_reply = response.text
    st.session_state.chat_history.append(("ai", ai_reply))
    st.markdown(f"**AI Teacher:** {ai_reply}")
    audio_b64 = speak_text(ai_reply)
    audio_html = f'<audio autoplay="true" src="data:audio/mp3;base64,{audio_b64}" controls></audio>'
    st.markdown(audio_html, unsafe_allow_html=True)

# Clear history button
if st.button("🗑️ Clear Conversation"):
    st.session_state.chat_history = []
    st.rerun()
