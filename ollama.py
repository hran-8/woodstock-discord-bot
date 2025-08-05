import aiohttp 
PERSONALITY = {
  "role": "system",
  "content": (
    "you are woodstock, a clever assistant"
    "do not repeat phrases or sentence structure"
    "do not drag out your sentences, keep your sentences short and snappy"
    "don't include quotation marks in your responses"
  )
}

async def query_ollama(model, history): 
    url="http://localhost:11434/api/chat"
    payload = {
        "model": model,
        "messages": history, 
        "stream": False,
    }


    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            return data.get("message", {}).get("content", "")