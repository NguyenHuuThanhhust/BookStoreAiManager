import logging
import os
import pyttsx3
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize voice engine
engine = pyttsx3.init()
engine.setProperty("rate", 160)
engine.setProperty("voice", engine.getProperty("voices")[1].id)  # choose voice (0=male, 1=female depending on system)


def speak_text(text: str, lang: str = "en"):
    """Convert text to speech."""
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        logging.error(f"Speech error: {str(e)}")


def chat_with_customer(question: str) -> str:
    """Customer chatbot - friendly assistant for book shopping."""
    system_prompt = (
        "You are a friendly bookstore assistant. "
        "You help customers find books, suggest books by genre, "
        "and answer basic questions about the bookstore."
    )

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=200
        )
        reply = response.choices[0].message.content.strip()
        speak_text(reply, lang="en")  # speak out the reply
        return reply
    except Exception as e:
        logging.error(f"chat_with_customer error: {str(e)}")
        return "Sorry, something went wrong. Please try again."


def chat_with_management(question: str, context: str = "") -> str:
    """
    Staff chatbot - bookstore management assistant.
    """
    system_prompt = (
        "You are a bookstore management assistant. "
        "You ONLY answer questions about:\n"
        "- Suggesting price adjustments based on sales.\n"
        "- Suggesting restocking books based on demand or inventory.\n"
        "- Tracking book market information.\n"
        "- Profit analysis or inventory optimization.\n"
        "If outside scope, reply: 'I only support bookstore management questions.'\n"
        f"Current data: {context}"
    )

    conversation = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation,
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"
