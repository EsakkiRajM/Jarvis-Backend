import os
import logging

from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field

from groq import Groq

from google import genai
from google.genai import types

from database import get_connection


# ============================================
# ENVIRONMENT CONFIGURATION
# ============================================

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s - %(levelname)s - "
        "%(name)s - %(message)s"
    )
)

logger = logging.getLogger("JARVIS")


# ============================================
# FASTAPI APPLICATION
# ============================================

app = FastAPI(
    title="JARVIS AI Backend",
    description="Personal AI Assistant",
    version="2.0.0"
)


# ============================================
# AI CONFIGURATION
# ============================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

PRIMARY_AI = os.getenv(
    "PRIMARY_AI",
    "groq"
).strip().lower()


if PRIMARY_AI not in ("groq", "gemini"):
    raise ValueError(
        "PRIMARY_AI must be groq or gemini"
    )


# ============================================
# GROQ CLIENT
# ============================================

groq_client = None

if GROQ_API_KEY:

    groq_client = Groq(
        api_key=GROQ_API_KEY,
        timeout=25.0,
        max_retries=0
    )


# ============================================
# GEMINI CLIENT
# ============================================

gemini_client = None

if GEMINI_API_KEY:

    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY,
        http_options=types.HttpOptions(
            timeout=25000
        )
    )


# ============================================
# JARVIS SYSTEM PROMPT
# ============================================

SYSTEM_PROMPT = """
You are JARVIS, a personal AI assistant.

Your owner's name is Esakki.

You are intelligent, friendly and helpful.

Give clear and accurate answers.

Keep answers conversational and concise.

Use Markdown formatting when necessary.

For programming questions, provide correct
and practical code examples.

Never claim that you performed an action
unless it was actually completed.
"""


# ============================================
# REQUEST MODEL
# ============================================

class ChatRequest(BaseModel):

    message: str = Field(
        min_length=1,
        max_length=10000
    )


# ============================================
# GROQ AI
# ============================================

def ask_groq(message: str):

    if not groq_client:
        raise RuntimeError(
            "Groq API key is not configured"
        )

    logger.info("Connecting to Groq...")

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
        raise RuntimeError(
            "Groq returned an empty response"
        )

    return reply


# ============================================
# GEMINI AI
# ============================================

def ask_gemini(message: str):

    if not gemini_client:
        raise RuntimeError(
            "Gemini API key is not configured"
        )

    logger.info("Connecting to Gemini...")

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
        raise RuntimeError(
            "Gemini returned an empty response"
        )

    return reply


# ============================================
# AI PROVIDER REGISTRY
# ============================================

AI_PROVIDERS = {
    "groq": ask_groq,
    "gemini": ask_gemini
}


# ============================================
# AI FALLBACK SYSTEM
# ============================================

def get_ai_response(message: str):

    fallback_ai = (
        "gemini"
        if PRIMARY_AI == "groq"
        else "groq"
    )

    providers = [
        PRIMARY_AI,
        fallback_ai
    ]

    for provider in providers:

        try:

            logger.info(
                "Trying provider: %s",
                provider.upper()
            )

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
                "%s failed: %s",
                provider.upper(),
                error,
                exc_info=True
            )

    logger.error("All AI providers failed")

    return {
        "success": False,
        "provider": None,
        "reply": (
            "Sorry Esakki, both AI providers "
            "are temporarily unavailable. "
            "Please try again later."
        )
    }


# ============================================
# AI ENDPOINT
# ============================================

@app.post("/ask-ai")
@app.post("/ask-gemini")
def ask_ai(request: ChatRequest):

    message = request.message.strip()

    if not message:

        raise HTTPException(
            status_code=400,
            detail="Please enter a message."
        )

    return get_ai_response(message)


# ============================================
# CORS CONFIGURATION
# ============================================

FRONTEND_ORIGINS = [

    origin.strip().rstrip("/")

    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173"
    ).split(",")

    if origin.strip()

]


app.add_middleware(

    CORSMiddleware,

    allow_origins=FRONTEND_ORIGINS,

    allow_credentials=True,

    allow_methods=[
        "GET",
        "POST",
        "OPTIONS"
    ],

    allow_headers=[
        "Content-Type",
        "Authorization"
    ]

)


# ============================================
# HEALTH CHECK
# ============================================

@app.get("/")
@app.get("/health")
def health_check():

    return {

        "success": True,

        "message": "JARVIS Backend Running",

        "status": "online",

        "primary_ai": PRIMARY_AI,

        "fallback_ai": (
            "gemini"
            if PRIMARY_AI == "groq"
            else "groq"
        )

    }


# ============================================
# USERS API
# ============================================

@app.get("/users")
def get_users():

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM users"
        )

        users = cursor.fetchall()

        return {
            "success": True,
            "users": users
        }

    except Exception:

        logger.exception(
            "Database error while fetching users"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve user information."
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================
# STARTUP LOGGING
# ============================================

@app.on_event("startup")
def startup_event():

    logger.info("JARVIS BACKEND STARTED")

    logger.info(
        "Primary AI: %s",
        PRIMARY_AI.upper()
    )

    logger.info(
        "Groq configured: %s",
        bool(groq_client)
    )

    logger.info(
        "Gemini configured: %s",
        bool(gemini_client)
    )

    logger.info(
        "Allowed frontend origins: %s",
        FRONTEND_ORIGINS
    )