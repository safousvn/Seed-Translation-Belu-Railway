import os
import asyncio
import httpx
from datetime import datetime

# ================= CONFIG =================
API_URL = "https://ark.ap-southeast.bytepluses.com/api/v3/responses"
MODEL = "seed-translation"
API_KEY = os.environ.get("ARK_API_KEY")

SOURCE_LANG = "English"
TARGET_LANG = "Vietnamese"
TEXT_SAMPLE = (
    "Artificial Intelligence is transforming industries globally and enabling new possibilities "
    "for automation, creativity, and communication. This text is used to stress-test translation throughput."
)

TARGET_TOKENS = 10_000_000  # goal
TARGET_HOURS = 5            # target time
AVG_TOKENS_PER_REQ = 1500   # adjust based on your observations
# ==========================================

TOTAL_SECONDS = TARGET_HOURS * 3600
TOTAL_REQUESTS = TARGET_TOKENS // AVG_TOKENS_PER_REQ
REQUESTS_PER_SECOND = TOTAL_REQUESTS / TOTAL_SECONDS

# Start with moderate concurrency, adjust dynamically
INITIAL_CONCURRENT_REQUESTS = max(5, int(REQUESTS_PER_SECOND * 1.5))


async def call_translation(client: httpx.AsyncClient, request_id: int):
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
        return await call_translation(client, request_id)


async def main():
    if not API_KEY:
        print("❌ Missing ARK_API_KEY environment variable")
        return

    print(f"🚀 Starting Auto-Scale Dynamic Seed Translation Runner at {datetime.now()}")

    total_tokens = 0
    request_counter = 0
    concurrency = INITIAL_CONCURRENT_REQUESTS
    sem = asyncio.Semaphore(concurrency)

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(headers=headers) as client:
        while total_tokens < TARGET_TOKENS:
            request_counter += 1

            # Adjust concurrency dynamically every 100 requests
            if request_counter % 100 == 0:
                elapsed_minutes = max(1, (datetime.now() - start_time).total_seconds() / 60)
                tokens_per_minute = total_tokens / elapsed_minutes
                target_per_minute = TARGET_TOKENS / (TARGET_HOURS * 60)
                if tokens_per_minute < target_per_minute:
                    concurrency = min(concurrency + 5, 200)
                elif tokens_per_minute > target_per_minute * 1.2:
                    concurrency = max(concurrency - 5, 5)
                sem = asyncio.Semaphore(concurrency)
                print(f"⚙️ Adjusted concurrency: {concurrency}, Tokens/min: {int(tokens_per_minute)}")

            task = asyncio.create_task(worker(client, sem, request_counter))
            tokens = await task
            total_tokens += tokens

            print(f"[{request_counter}] +{tokens} tokens | Total={total_tokens:,}")

    print(f"🏁 Target reached: {total_tokens:,} tokens in {(datetime.now() - start_time)}")


if __name__ == "__main__":
    start_time = datetime.now()
    asyncio.run(main())
