dp = Dispatcher()

# =====================
# 🧠 ПАМЯТЬ
# =====================
memory = {}

def get_memory(user_id: int):
    return memory.get(user_id, [])

def add_memory(user_id: int, role: str, text: str):
    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append({"role": role, "text": text})

    # ограничение памяти
    memory[user_id] = memory[user_id][-MAX_MEMORY:]


# =====================
# 🤖 ЗАПРОС К OPENROUTER (БЫСТРЫЙ)
# =====================
async def ask_ai(messages):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            data = await resp.json()
            return data["choices"][0]["message"]["content"]


# =====================
# 🚀 START
# =====================
@dp.message(CommandStart())
async def start(msg: types.Message):
    await msg.answer("🤖 AI бот запущен! Напиши сообщение.")

# =====================
# 💬 ОСНОВНОЙ ХЕНДЛЕР
# =====================
@dp.message()
async def chat(msg: types.Message):
    user_id = msg.from_user.id
    user_text = msg.text

    # анти-спам минимальный
    await msg.chat.do("typing")

    # память
    add_memory(user_id, "user", user_text)

    messages = [
        {"role": "system", "content": "Ты умный, быстрый и краткий AI ассистент."}
    ]

    for m in get_memory(user_id):
        messages.append({
            "role": m["role"],
            "content": m["text"]
        })

    try:
        answer = await ask_ai(messages)

        add_memory(user_id, "assistant", answer)

        await msg.answer(answer)

    except Exception as e:
        await msg.answer("⚠️ Ошибка AI запроса")
        print("ERROR:", e)


# =====================
# ▶️ RUN
# =====================
async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
