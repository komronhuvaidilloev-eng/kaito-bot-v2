import os
import asyncio
import logging
from aiohttp import web, ClientSession
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "openai/gpt-4o-mini"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Временная память: последние 10 сообщений каждого пользователя
memory = {}


def add_memory(user_id, role, text):
    memory.setdefault(user_id, [])
    memory[user_id].append({"role": role, "content": text})
    memory[user_id] = memory[user_id][-10:]


async def ask_ai(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500,
    }

    async with ClientSession() as session:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        ) as response:
            data = await response.json()

            if response.status != 200:
                raise Exception(str(data))

            return data["choices"][0]["message"]["content"]


@dp.message(CommandStart())
async def start_command(message: types.Message):
    await message.answer("🤖 Я работаю! Напиши мне сообщение.")


@dp.message()
async def chat(message: types.Message):
    if not message.text:
        return

    user_id = message.from_user.id
    add_memory(user_id, "user", message.text)

    messages = [
        {
            "role": "system",
            "content": "Ты полезный, дружелюбный и краткий AI-ассистент. Отвечай на языке пользователя."
        }
    ] + memory[user_id]

    try:
        answer = await ask_ai(messages)
        add_memory(user_id, "assistant", answer)
        await message.answer(answer)
    except Exception as error:
        print(f"AI ERROR: {error}")
        await message.answer("Сейчас не получилось получить ответ от AI. Попробуй ещё раз.")


# Этот маленький сервер нужен только Render, чтобы он видел открытый порт.
async def health_check(request):
    return web.Response(text="Kaito bot is running")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"WEB SERVER STARTED ON PORT {port}")


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден в Render Environment Variables")

    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY не найден в Render Environment Variables")

    await start_web_server()
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
