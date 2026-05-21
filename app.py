import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import base64
import tempfile
import os

st.set_page_config(page_title="AI English Teacher – Voice + Text", page_icon="🎙️", layout="centered")

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

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "audio_html" not in st.session_state:
    st.session_state.audio_html = ""

# Gemini API Key
api_key = st.text_input("🔑 Google Gemini API Key (get free at https://aistudio.google.com)", type="password")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.warning("Please enter your Gemini API key to enable AI answers.")
    model = None

# Function to speak text (gTTS works on cloud)
def speak_text(text):
    tts = gTTS(text=text, lang="en")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tts.save(f.name)
        with open(f.name, "rb") as audio_file:
            audio_bytes = audio_file.read()
        os.unlink(f.name)
    b64 = base64.b64encode(audio_bytes).decode()
    return f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}" controls></audio>'

# JavaScript for browser voice recognition (no Python library)
voice_recognition_html = """
<div id="voice-input" style="text-align:center; margin:1rem 0;">
    <button id="start-recognition" style="background-color:#ff9a3c; border:none; border-radius:50px; padding:0.5rem 1rem; font-size:1.2rem; cursor:pointer;">🎤 Speak your question</button>
    <p id="result" style="color:white; margin-top:0.5rem;"></p>
</div>
<script>
    const startBtn = document.getElementById('start-recognition');
    const resultDiv = document.getElementById('result');
    startBtn.addEventListener('click', () => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            resultDiv.innerText = 'Your browser does not support speech recognition. Try Chrome, Edge, or Safari.';
            return;
        }
        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        recognition.start();
        resultDiv.innerText = 'Listening...';
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            resultDiv.innerText = 'You said: ' + transcript;
            // Send to Streamlit using Streamlit.setComponentValue
            const streamlitData = { transcript: transcript };
            // This custom event will be caught by a hidden Streamlit component
            const setValue = new CustomEvent('streamlit:setComponentValue', { detail: streamlitData });
            window.dispatchEvent(setValue);
        };
        recognition.onerror = (event) => {
            resultDiv.innerText = 'Error: ' + event.error;
        };
    });
</script>
"""

# To receive the transcript, we need a tiny custom component. Simpler: use a hidden text input that gets updated via JavaScript.
# But Streamlit doesn't easily allow JavaScript to set Python variables. Alternative: use st.text_input and let user paste or type.
# For simplicity, I'll keep the voice button as a fun UI element, but actual voice-to-text still requires a Python library.
# However, we CAN use `streamlit-webrtc` or `streamlit-mic-recorder` but those require extra setup.

# Given the complexity, I'll provide a robust solution using `streamlit-mic-recorder` which works on cloud.
# Install: pip install streamlit-mic-recorder
# This component records audio in browser and sends it as bytes to Python. Then we use a free speech-to-text API.

# But to keep it minimal, I'll give the final working version using `streamlit-mic-recorder`.

st.markdown("## 🎙️ AI English Teacher")
st.markdown("Ask me anything – you can **type** or **use the microphone** (click the button below).")

# Install streamlit-mic-recorder in requirements.txt: streamlit-mic-recorder
from streamlit_mic_recorder import mic_recorder

audio = mic_recorder(start_prompt="🎤 Click to speak", stop_prompt="⏹️ Stop", key="recorder")

if audio:
    st.audio(audio['bytes'], format="audio/wav")
    # Transcribe using Google Speech Recognition (still needs internet)
    import speech_recognition as sr
    import io
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(audio['bytes'])) as source:
            recorded = recognizer.record(source)
            user_text = recognizer.recognize_google(recorded)
            st.success(f"📝 You said: {user_text}")
    except Exception as e:
        st.error(f"Could not transcribe: {e}")
        user_text = None

    if user_text and model:
        st.session_state.chat_history.append(("user", user_text))
        with st.spinner("🤖 Thinking..."):
            response = model.generate_content(user_text)
            ai_reply = response.text
        st.session_state.chat_history.append(("ai", ai_reply))
        st.markdown(f"**AI Teacher:** {ai_reply}")
        # Speak
        audio_html = speak_text(ai_reply)
        st.markdown(audio_html, unsafe_allow_html=True)

# Text input fallback
user_text_input = st.text_input("Or type your question here", key="text_input")
if st.button("Send") and user_text_input and model:
    st.session_state.chat_history.append(("user", user_text_input))
    with st.spinner("🤖 Thinking..."):
        response = model.generate_content(user_text_input)
        ai_reply = response.text
    st.session_state.chat_history.append(("ai", ai_reply))
    st.markdown(f"**AI Teacher:** {ai_reply}")
    audio_html = speak_text(ai_reply)
    st.markdown(audio_html, unsafe_allow_html=True)

# Display chat history
st.markdown("---")
for role, msg in st.session_state.chat_history:
    st.markdown(f"**{role.capitalize()}:** {msg}")

if st.button("🗑️ Clear history"):
    st.session_state.chat_history = []
    st.rerun()
