import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL = os.environ.get("REPOMIND_MODEL", "gemini-3.1-flash-lite")

_client = None


def get_client():

    global _client

    if _client is None:
        _client = genai.Client(
            api_key=os.environ["GEMINI_API_KEY"]
        )

    return _client


def generate(system_prompt, user_message, max_output_tokens=1200, client=None):

    active_client = client or get_client()

    response = active_client.models.generate_content(
        model=MODEL,
        contents=user_message,
        config={
            "system_instruction": system_prompt,
            "max_output_tokens": max_output_tokens
        }
    )

    return response.text or ""