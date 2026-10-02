import os

from dotenv import load_dotenv
from google import genai

from limiter import wait_for_slot

load_dotenv()
PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
if PROVIDER != "gemini":
    raise NotImplementedError(f"provider {PROVIDER} is not wired yet")
client = genai.Client()
model = os.getenv("GEMINI_CHAT_MODEL")
tokens_in_total = 0
tokens_out_total = 0
MAX_CALLS = int(os.getenv("MAX_CALLS", "50"))
calls_made = 0

def ask(prompt):
    global tokens_in_total, tokens_out_total, calls_made
    if calls_made >= MAX_CALLS:
        raise RuntimeError("MAX_CALLS reached, stopping")
    wait_for_slot()
    calls_made += 1
    response = client.models.generate_content(model=model, contents=prompt)
    tokens_in_total += response.usage_metadata.prompt_token_count
    tokens_out_total += response.usage_metadata.candidates_token_count
    return response.text

