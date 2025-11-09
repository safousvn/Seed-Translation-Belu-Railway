import os
import time
import requests
import threading
from datetime import datetime

# ============ CONFIG ============
API_URL = "https://ark.ap-southeast.bytepluses.com/api/v3/responses"
MODEL = "seed-translation-250915"
API_KEY = os.environ.get("ARK_API_KEY")

SOURCE_LANG = "en"
TARGET_LANG = "vi"
TEXT_SAMPLE = (
    "Artificial Intelligence is transforming industries globally and enabling new possibilities "
    "for automation, creativity, and communication. This is a stress test for translation throughput."
)

THREAD_COUNT = 10          # number of threads running in parallel
REQUESTS_PER_THREAD = 1000 # how many requests per thread
DELAY_BETWEEN_CALLS = 0.5  # seconds between each call in a thread
# ===============================


def call_seed_translation(thread_id, results):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    total_tokens = 0

    for i in range(REQUESTS_PER_THREAD):
        payload = {
            "model": MODEL,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"Translate the following text from {SOURCE_LANG} to {TARGET_LANG}: {TEXT_SAMPLE}"
                        }
                    ]
                }
            ]
        }

        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=10)
            data = resp.json()

            if "error" in data:
                print(f"[T{thread_id} #{i}] ❌ Error: {data['error']['message']}")
                time.sleep(1)
                continue

            tokens = data.get("usage", {}).get("total_tokens", 0)
            total_tokens += tokens

            print(f"[T{thread_id} #{i}] ✅ +{tokens} tokens (Total: {total_tokens:,})")

        except Exception as e:
            print(f"[T{thread_id} #{i}] ⚠️ Exception: {str(e)}")

        time.sleep(DELAY_BETWEEN_CALLS)

    results[thread_id] = total_tokens
    print(f"🧵 Thread-{thread_id} done. Tokens used: {total_tokens:,}")


def main():
    if not API_KEY:
        print("❌ Missing environment variable: ARK_API_KEY")
        return

    print(f"🚀 Starting Seed Translation Parallel Runner at {datetime.now()}")
    print(f"Threads: {THREAD_COUNT}, Requests/thread: {REQUESTS_PER_THREAD}\n")

    threads = []
    results = {}

    for t_id in range(THREAD_COUNT):
        t = threading.Thread(target=call_seed_translation, args=(t_id, results))
        t.start()
        threads.append(t)
        time.sleep(0.3)  # small stagger

    for t in threads:
        t.join()

    total = sum(results.values())
    print(f"🏁 Finished all threads — Total tokens used: {total:,}")


if __name__ == "__main__":
    main()
