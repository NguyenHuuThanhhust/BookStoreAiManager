import logging
from speech_recognition import Recognizer, Microphone
from deep_translator import GoogleTranslator
import pyttsx3

# Initialize pyttsx3 once (avoid re-init every call)
engine = pyttsx3.init()
engine.setProperty("rate", 160)  #speech speed
voices = engine.getProperty("voices")
if len(voices) > 1:
    engine.setProperty("voice", voices[1].id)   #choose voice (0=male, 1=female depending on system)


def recognize_speech(language='en-US'):
    """Capture speech from microphone and convert to text."""
    recognizer = Recognizer()
    with Microphone() as source:
        print("🎤 Listening...")
        audio = recognizer.listen(source)

        try:
            return recognizer.recognize_google(audio, language=language)
        except Exception:
            return ""


def translate_text(text, src="auto", dest="en"):
    """Translate text using Google Translator (deep-translator)."""
    try:
        return GoogleTranslator(source=src, target=dest).translate(text)
    except Exception as e:
        print(f"❌ Cannot translate: {e}")
        return text


def speak_text(text, lang='en'):
    """Speak text aloud using pyttsx3 (offline)."""
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        logging.error(f"❌ Error in speak_text: {e}")
