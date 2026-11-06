
import os
import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from groq import Groq
from google import genai
from google.genai import types

from database import get_connection


# --------------------------------
# ENVIRONMENT CONFIGURATION
# --------------------------------

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JARVIS")

app = FastAPI(title="JARVIS AI Backend")


# --------------------------------
# AI PROVIDER CONFIGURATION
# --------------------------------

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Choose primary AI from .env
PRIMARY_AI = os.getenv("PRIMARY_AI", "groq").strip().lower()

if PRIMARY_AI not in ["groq", "gemini"]:
    raise ValueError("PRIMARY_AI must be either 'groq' or 'gemini'")


# Initialize Groq
groq_client = (
    Groq(
        api_key=GROQ_API_KEY,
        timeout=25.0,
        max_retries=0
    )
    if GROQ_API_KEY else None
)


# Initialize Gemini
gemini_client = (
    genai.Client(
        api_key=GEMINI_API_KEY,
        http_options=types.HttpOptions(
            timeout=25000
        )
    )
    if GEMINI_API_KEY else None
)


# --------------------------------
# JARVIS SYSTEM INSTRUCTION
# --------------------------------

SYSTEM_PROMPT = """
You are Jarvis, a personal AI assistant.

Your owner's name is Esakki.

Give clear, friendly and helpful answers.
Keep answers conversational.
Be intelligent and concise.
"""


# --------------------------------
# REQUEST MODEL
# --------------------------------

class ChatRequest(BaseModel):
    message: str


# --------------------------------
# GROQ AI FUNCTION
# --------------------------------

def ask_groq(message: str):

    if not groq_client:
        raise RuntimeError("Groq API key is not configured")

    logger.info("Trying Groq AI...")

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",

        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": message
            }
        ],

        max_completion_tokens=1024
    )

    reply = response.choices[0].message.content

    if not reply:
        raise RuntimeError("Groq returned an empty response")

    return reply


# --------------------------------
# GEMINI AI FUNCTION
# --------------------------------

def ask_gemini(message: str):

    if not gemini_client:
        raise RuntimeError("Gemini API key is not configured")

    logger.info("Trying Gemini AI...")

    response = gemini_client.models.generate_content(
        model="gemini-3.5-flash",

        contents=message,

        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=1024
        )
    )

    reply = response.text

    if not reply:
        raise RuntimeError("Gemini returned an empty response")

    return reply


# --------------------------------
# AI PROVIDER SELECTION
# --------------------------------

AI_PROVIDERS = {
    "groq": ask_groq,
    "gemini": ask_gemini
}


def get_ai_response(message: str):

    # Primary provider comes first.
    # The other provider automatically becomes the fallback.

    fallback_ai = "gemini" if PRIMARY_AI == "groq" else "groq"

    provider_order = [
        PRIMARY_AI,
        fallback_ai
    ]

    for provider in provider_order:

        try:

            logger.info("Using AI provider: %s", provider.upper())

            reply = AI_PROVIDERS[provider](message)

            logger.info(
                "%s response successful",
                provider.upper()
            )

            return {
                "success": True,
                "provider": provider,
                "reply": reply
            }

        except Exception as error:

            logger.error(
                "%s failed: %s: %s",
                provider.upper(),
                type(error).__name__,
                error
            )

            logger.info(
                "Switching to the next AI provider..."
            )

    return {
        "success": False,
        "provider": None,
        "reply": "Sorry Esakki, both Groq and Gemini are temporarily unavailable. Please try again later."
    }


# --------------------------------
# MAIN AI ENDPOINT
# --------------------------------

@app.post("/ask-ai")
@app.post("/ask-gemini")
def ask_ai(request: ChatRequest):

    message = request.message.strip()

    if not message:

        return {
            "success": False,
            "reply": "Please enter a message."
        }

    return get_ai_response(message)


# --------------------------------
# CORS CONFIGURATION
# --------------------------------

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# --------------------------------
# HOME API
# --------------------------------

@app.get("/")
def home():

    return {
        "message": "JARVIS Backend Running",
        "status": "online",
        "primary_ai": PRIMARY_AI
    }


# --------------------------------
# USERS API
# --------------------------------

@app.get("/users")
def get_users():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

        return {
            "users": users
        }

    finally:

        cursor.close()
        connection.close()
