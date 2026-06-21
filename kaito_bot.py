import asyncio
import requests
import os
from aiogram import Bot, Dispatcher, types

# 🔐 ключи берутся из Render (Environment Variables)
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🧠 память (временная)
memory = {}

def ask_ai(user_id, text):
    url = "https://openrouter.ai/api/v1/chat/completions"

    history = memory.get(user_id, [])
    history.append({"role": "user", "content": text})
    history = history[-10:]
    memory[user_id] = history

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta-llama/llama-3.1-8b-instruct",
        "messages": history
    }

    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        result = r.json()

        if "choices" not in result:
            return f"Ошибка API: {result}"

        answer = result["choices"][0]["message"]["content"]

        history.append({"role": "assistant", "content": answer})
        memory[user_id] = history

        return answer

    except Exception as e:
        return f"Ошибка: {e}"


@dp.message()
async def handler(message: types.Message):
    response = ask_ai(message.from_user.id, message.text)
    await message.answer(response)


async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())