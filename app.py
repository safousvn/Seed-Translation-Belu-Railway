import os
import time
import requests
from datetime import datetime

# =================== CONFIG ======================
API_URL = "https://ark.ap-southeast.bytepluses.com/api/v3/responses"
MODEL = "seed-translation-250915"
API_KEY = os.environ.get("ARK_API_KEY")

SOURCE_LANG = "en"
TARGET_LANG = "vi"
TEXT_SAMPLE = "Artificial Intelligence is transforming industries globally and enabling new possibilities."

REQUESTS_PER_MIN = 60       # how many API calls per minute
MAX_REQUESTS = 5000         # total requests per run
# =================================================


def call_seed_translation():
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": TEXT_SAMPLE}
                ]
            }
        ],
        "parameters": {
            "source_language": SOURCE_LANG,
            "target_language": TARGET_LANG
        }
    }

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        data = resp.json()

        if "error" in data:
            return None, data["error"]["message"], 0

        output_text = data["output"][0]["content"][0]["text"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return output_text, None, tokens

    except Exception as e:
        return None, str(e), 0


def main():
    if not API_KEY:
        print("❌ Missing environment variable: ARK_API_KEY")
        return

    print(f"🚀 Starting Seed Translation Auto-Runner at {datetime.now()}")
    total_tokens = 0
    delay = 60 / REQUESTS_PER_MIN

    for i in range(1, MAX_REQUESTS + 1):
        output, error, tokens = call_seed_translation()

        if error:
            print(f"[{i}] ❌ Error: {error}")
            time.sleep(2)
            continue

        total_tokens += tokens
        print(f"[{i}] ✅ {tokens} tokens | Total = {total_tokens:,}")

        time.sleep(delay)

    print(f"🏁 Finished {MAX_REQUESTS} requests — Total tokens used: {total_tokens:,}")


if __name__ == "__main__":
    main()
