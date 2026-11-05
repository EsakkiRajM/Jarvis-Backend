import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

client = Groq(api_key=api_key)

try:
    print("Connecting to Groq...", flush=True)

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "You are Jarvis, an intelligent AI assistant. Respond naturally and concisely."
            },
            {
                "role": "user",
                "content": "Hello Jarvis! Introduce yourself."
            }
        ],
        timeout=30
    )

    print("\nGroq Response:", flush=True)

    print(
        response.choices[0].message.content,
        flush=True
    )

except Exception as e:
    print("\nGroq Error:", flush=True)
    print("Error Type:", type(e).__name__, flush=True)
    print("Details:", str(e), flush=True)