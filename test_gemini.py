import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

try:
    print("Connecting to Gemini...", flush=True)

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents="Hello Jarvis! Introduce yourself."
    )

    print("\nGemini Response:")
    print(response.text)

except Exception as e:
    print("\nGemini Error:")
    print(type(e).__name__)
    print(str(e))