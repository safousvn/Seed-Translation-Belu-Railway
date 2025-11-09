import os
import time
import requests
import random

# ---- CONFIG ----
API_URL = "https://ark.ap-southeast.bytepluses.com/api/v3/chat/completions"
API_KEY = os.environ.get("ARK_API_KEY")  # Set in environment (Railway secret)
MODEL = "seed-translation"
SOURCE_LANG = "en"
TARGET_LANG = "vi"

# Example text (you can load bigger content)
TEXT_SAMPLE = "This is a sample sentence to be translated repeatedly."

# ---- MAIN LOOP ----
def call_translation_api():
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": f"Translate from {SOURCE_LANG} to {TARGET_LANG}."},
            {"role": "user", "content": TEXT_SAMPLE}
        ]
    }
    resp = requests.post(API_URL, json=payload, headers=headers)
    data = resp.json()
    try:
        tokens = data["usage"]["total_tokens"]
    except Exception:
        tokens = 0
    print(f"[{time.ctime()}] ✅ Tokens used this call: {tokens}")
    return tokens


if __name__ == "__main__":
    total_tokens = 0
    start_time = time.time()
    while time.time() - start_time < 5 * 3600:  # run for 5 hours
        tokens = call_translation_api()
        total_tokens += tokens
        print(f"Total tokens so far: {total_tokens}")
        time.sleep(random.uniform(2, 5))  # delay between calls
