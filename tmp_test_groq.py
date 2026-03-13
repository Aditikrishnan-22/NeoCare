import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/chat/completions"

async def test_groq():
    if not api_key:
        print("Error: GROQ_API_KEY not found in .env")
        return
    print(f"Testing with key starting with: {api_key[:10]}...")
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": "Hello, are you working?"}],
        "max_tokens": 10
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"}
            )
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print("Success! Reply:", resp.json()["choices"][0]["message"]["content"])
            else:
                print("Error:", resp.text)
        except Exception as e:
            print(f"Exception: {e}")

asyncio.run(test_groq())
