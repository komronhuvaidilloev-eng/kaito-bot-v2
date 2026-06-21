import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
import aiohttp

# --------------------
# TOKENS (через Render ENV)
# --------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "openai/gpt-4o-mini"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --------------------
# MEMORY
# --------------------
memory = {}

def add_memory(user_id, role, text):
    if user_id not in memory:
        memory[user_id] = []
    memory[user_id].append({"role": role, "text": text})
    memory[user_id] = memory[user_id][-10:]

def get_memory(user_id):
    return memory.get(user_id, [])

# --------------------
# AI REQUEST
# --------------------
async def ask_ai(messages):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as r:
            res = await r.json()
            return res["choices"][0]["message"]["content"]

# --------------------
# START
# --------------------
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("🤖 AI бот работает!")

# --------------------
# CHAT
# --------------------
@dp.message()
async def chat(message: types.Message):
    user_id = message.from_user.id
    text = message.text

    add_memory(user_id, "user", text)

    msgs = [{"role": "system", "content": "Ты полезный и краткий ассистент."}]

    for m in get_memory(user_id):
        msgs.append({"role": m["role"], "content": m["text"]})

    try:
        answer = await ask_ai(msgs)
        add_memory(user_id, "assistant", answer)
        await message.answer(answer)
    except Exception as e:
        await message.answer("Ошибка AI")
        print(e)

# --------------------
# RUN
# --------------------
async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
