import os
import asyncio
import httpx
from datetime import datetime, timedelta

# ================= CONFIG =================
API_URL = "https://ark.ap-southeast.bytepluses.com/api/v3/responses"
MODEL = "seed-translation-250915"
API_KEY = os.environ.get("ARK_API_KEY")

SOURCE_LANG = "en"
TARGET_LANG = "vi"
TEXT_SAMPLE = (
    "Artificial Intelligence is transforming industries globally and enabling new possibilities "
    "for automation, creativity, and communication. This text is used to stress-test token consumption."
)

TARGET_TOKENS = 10_000_000      # goal: consume 10M tokens
TARGET_HOURS = 5                # within 5 hours
# ==========================================

# Calculate approximate concurrency
TOTAL_SECONDS = TARGET_HOURS * 3600
# Estimate average tokens per request
AVG_TOKENS_PER_REQ = 1500  # adjust based on real usage
TOTAL_REQUESTS = TARGET_TOKENS // AVG_TOKENS_PER_REQ
REQUESTS_PER_SECOND = TOTAL_REQUESTS / TOTAL_SECONDS
CONCURRENT_REQUESTS = max(10, int(REQUESTS_PER_SECOND * 2))  # double to avoid idle time


async def call_translation(client: httpx.AsyncClient, request_id: int):
    payload = {
        "model": MODEL,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": TEXT_SAMPLE},
                    {
                        "type": "translation_options",
                        "translation_options": {
                            "source_language": SOURCE_LANG,
                            "target_language": TARGET_LANG
                        }
                    }
                ]
            }
        ]
    }

    try:
        resp = await client.post(API_URL, json=payload, timeout=20.0)
        data = resp.json()
        if "error" in data:
            print(f"[Req {request_id}] ❌ {data['error']['message']}")
            return 0
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return tokens
    except Exception as e:
        print(f"[Req {request_id}] ⚠️ Exception: {e}")
        return 0


async def worker(client: httpx.AsyncClient, sem: asyncio.Semaphore, request_id: int):
    async with sem:
        tokens = await call_translation(client, request_id)
        return tokens


async def main():
    if not API_KEY:
        print("❌ Missing ARK_API_KEY environment variable")
        return

    print(f"🚀 Starting Auto-Scale Seed Translation at {datetime.now()}")
    total_tokens = 0
    request_counter = 0

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    sem = asyncio.Semaphore(CONCURRENT_REQUESTS)

    async with httpx.AsyncClient(headers=headers) as client:
        start_time = datetime.now()
        while total_tokens < TARGET_TOKENS:
            request_counter += 1
            tokens = await worker(client, sem, request_counter)
            total_tokens += tokens
            elapsed = (datetime.now() - start_time).total_seconds() / 60
            tps = total_tokens / elapsed if elapsed > 0 else 0

            print(f"[{request_counter}] +{tokens} tokens | Total={total_tokens:,} | "
                  f"Tokens/min≈{int(tps*60)}")

    print(f"🏁 Goal reached: {total_tokens:,} tokens in {(datetime.now() - start_time)}")


if __name__ == "__main__":
    asyncio.run(main())
