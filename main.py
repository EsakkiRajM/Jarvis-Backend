from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import get_connection

from google import genai
from google.genai import types, errors

from dotenv import load_dotenv
import time
import os

load_dotenv()

app = FastAPI()

# Initialize Gemini
api_key = os.getenv("GEMINI_API_KEY")

#print("API Key Loaded:", bool(api_key))

client = genai.Client(api_key=api_key)


class ChatRequest(BaseModel):
    message: str


@app.post("/ask-gemini")
def ask_gemini(request: ChatRequest):

    for attempt in range(3):

        try:

            print(f"Gemini request attempt: {attempt + 1}")

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=request.message,

                config=types.GenerateContentConfig(

                    system_instruction="""
                    You are Jarvis, a personal AI assistant.

                    Your owner's name is Esakki.

                    Give clear, friendly and helpful answers.
                    Keep answers conversational.
                    """

                )
            )

            return {
                "success": True,
                "reply": response.text
            }

        except errors.APIError as e:

            print(f"Gemini API Error: {e}")

            if getattr(e, "code", None) == 503 and attempt < 2:

                time.sleep(2 ** (attempt + 1))
                continue

            return {
                "success": False,
                "reply": "Gemini is temporarily unavailable. Please try again."
            }

        except Exception as e:

            print(f"Unexpected Error: {e}")

            return {
                "success": False,
                "reply": "Something went wrong. Please try again."
            }


    return {
        "success": False,
        "reply": "Gemini is currently unavailable."
    }


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


@app.get("/")
def home():

    return {
        "message": "JARVIS Backend Running"
    }


@app.get("/users")
def get_users():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("SELECT * FROM users")

    users = cursor.fetchall()

    connection.close()

    return {
        "users": users
    }