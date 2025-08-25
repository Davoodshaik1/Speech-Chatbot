import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import os
import requests
import time
import tempfile
import base64

# OpenRouter API setup
OR_API_KEY = "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"
OR_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Speech-to-Text (STT) Component
def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Please speak within 10 seconds.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
            text = recognizer.recognize_google(audio)
            return text
        except sr.WaitTimeoutError:
            st.error("Timeout: No speech detected within 10 seconds.")
            return None
        except sr.UnknownValueError:
            st.error("Sorry, I couldn't understand what you said.")
            return None
        except sr.RequestError as e:
            st.error(f"Sorry, there was an issue with the speech service: {e}")
            return None

# Text-to-Speech (TTS) Component
def text_to_speech(text):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_file.name)
            return temp_file.name
    except Exception as e:
        st.error(f"Failed to generate audio: {e}")
        return None

# LLM Response using OpenRouter API with Retry
def get_llm_response(input_text, user_name):
    headers = {
        "Authorization": f"Bearer {OR_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "meta-llama/llama-3.1-8b-instruct",
        "messages": [
            {"role": "system", "content": f"You are Speech Chat Bot, an AI assistant. The user's name is {user_name}. Provide concise, professional, and helpful answers, using the user's name where appropriate."},
            {"role": "user", "content": input_text}
        ],
        "max_tokens": 150,
        "temperature": 0.7
    }
    max_retries = 3
    retry_delay = 2
    for attempt in range(max_retries):
        try:
            response = requests.post(OR_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 503:
                st.warning(f"Attempt {attempt + 1}/{max_retries}: Service Unavailable. Retrying...")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
            st.error(f"OpenRouter error: {e}")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            return None

# Function to play audio in Streamlit and stop previous audio
def autoplay_audio(file_path, audio_placeholder):
    if file_path and os.path.exists(file_path):
        with open(file_path, "rb") as f:
            audio_bytes = f.read()
        b64 = base64.b64encode(audio_bytes).decode()
        audio_placeholder.empty()  # Stop previous audio
        audio_html = f"""
            <audio autoplay="true" style="display:none;">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
        """
        audio_placeholder.markdown(audio_html, unsafe_allow_html=True)
        time.sleep(1)  # Ensure playback starts before cleanup
        os.unlink(file_path)
    else:
        st.error("Audio file not found or invalid.")

# Streamlit UI
def main():
    # CSS with lively black background and dynamic animations
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #1A1A1A, #2A2A2A, #333333);
            color: #FFFFFF;
            font-family: 'Arial', sans-serif;
            overflow-x: hidden;
            min-height: 100vh;
        }
        .header {
            position: fixed;
            top: 0;
            width: 100%;
            background: rgba(0, 0, 0, 0.9);
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            z-index: 1000;
            border-bottom: 1px solid #444444;
            animation: fadeIn 1s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .header a {
            color: #1E90FF;
            text-decoration: none;
            margin-left: 20px;
            font-size: 1.1em;
            animation: slideIn 1s ease-out;
        }
        @keyframes slideIn {
            from { transform: translateX(-100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .title {
            font-size: 3em;
            text-align: center;
            color: #FFFFFF;
            margin-top: 60px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.7);
            animation: scaleUp 1.5s ease-out;
        }
        @keyframes scaleUp {
            from { transform: scale(0.8); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }
        .subtitle {
            font-size: 1.2em;
            text-align: center;
            color: #E0E0E0;
            margin-bottom: 40px;
            animation: fadeInUp 1.5s ease-in;
        }
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .stButton>button {
            background-color: #1E90FF;
            color: #FFFFFF;
            border-radius: 5px;
            padding: 10px 20px;
            font-size: 1.2em;
            border: none;
            box-shadow: 0 4px 10px rgba(30, 144, 255, 0.3);
            transition: all 0.3s ease;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        .stButton>button:hover {
            background-color: #104E8B;
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(30, 144, 255, 0.5);
        }
        .response-box {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 8px;
            margin: 20px auto;
            color: #FFFFFF;
            font-size: 1.1em;
            max-width: 600px;
            text-align: center;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);
            animation: slideInUp 1s ease-out;
        }
        @keyframes slideInUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .stTextInput>div>input {
            background-color: rgba(255, 255, 255, 0.1);
            color: #FFFFFF;
            border: 1px solid #1E90FF;
            border-radius: 5px;
            padding: 10px;
            font-size: 1em;
            animation: fadeIn 1s ease-in;
        }
        .stTextInput>label {
            color: #FFFFFF;
            font-size: 1.1em;
            animation: fadeIn 1s ease-in;
        }
        .highlight-box {
            background: rgba(30, 144, 255, 0.1);
            padding: 15px;
            border-radius: 8px;
            margin: 10px auto;
            color: #FFFFFF;
            font-size: 1em;
            max-width: 600px;
            text-align: left;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);
            animation: bounceIn 1s ease-out;
        }
        @keyframes bounceIn {
            0% { transform: scale(0.9); opacity: 0; }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); opacity: 1; }
        }
        </style>
    """, unsafe_allow_html=True)

    # Header with navigation
    st.markdown('<div class="header"><span>Speech Chat Bot</span><div><a href="#">Features</a><a href="#">About</a><a href="#">Help</a></div></div>', unsafe_allow_html=True)

    # Title and subtitle
    st.markdown('<h1 class="title">Innovative Voice Solutions for Seamless Interaction</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI-Powered Voice Assistance Built for Users Worldwide</p>', unsafe_allow_html=True)

    # Placeholder for audio
    audio_placeholder = st.empty()

    # Placeholder for response text
    response_placeholder = st.empty()

    # Initialize session state for user name
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None

    # Ask for name manually on first load
    if st.session_state.user_name is None:
        name_placeholder = st.empty()
        with name_placeholder.container():
            st.write("Please enter your name to begin:")
            user_name = st.text_input("Your Name", key="name_input", placeholder="e.g., John")
            if user_name:
                st.session_state.user_name = user_name.capitalize()
                welcome = f"Welcome, {st.session_state.user_name}. This is Speech Chat Bot, your professional voice assistant."
                response_placeholder.markdown(f'<div class="response-box">{welcome}</div>', unsafe_allow_html=True)
                welcome_audio = text_to_speech(welcome)
                if welcome_audio:
                    autoplay_audio(welcome_audio, audio_placeholder)
                # Delay to ensure full audio playback (approx. 6 seconds for 10 words)
                time.sleep(6)
                name_placeholder.empty()
                st.experimental_rerun()

    # Show "Record" button and key highlights after name is entered
    else:
        # Key Highlights Section
        st.markdown("### Key Features")
        st.markdown('<div class="highlight-box">• <strong>Voice Interaction:</strong> Speak naturally and receive instant audio responses.</div>', unsafe_allow_html=True)
        st.markdown('<div class="highlight-box">• <strong>Real-Time Transcription:</strong> See responses as they’re spoken for clarity.</div>', unsafe_allow_html=True)
        st.markdown('<div class="highlight-box">• <strong>Personalized Experience:</strong> Enjoy tailored responses with your name.</div>', unsafe_allow_html=True)
        st.markdown('<div class="highlight-box">• <strong>Seamless Audio:</strong> Previous responses stop when new queries begin.</div>', unsafe_allow_html=True)

        if st.button("🎙️ Record"):
            with st.spinner("Listening..."):
                user_input = speech_to_text()
                if user_input:
                    with st.spinner("Processing..."):
                        llm_response = get_llm_response(user_input, st.session_state.user_name)
                        if llm_response:
                            audio_file = text_to_speech(llm_response)
                            if audio_file:
                                response_placeholder.markdown(f'<div class="response-box">{llm_response}</div>', unsafe_allow_html=True)
                                autoplay_audio(audio_file, audio_placeholder)

if __name__ == "__main__":
    main()
