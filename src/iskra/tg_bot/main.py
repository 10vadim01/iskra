import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
import aiohttp

logging.basicConfig(level=logging.INFO)

token = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=token)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hello!")

@dp.message()
async def handle_user_message(message: types.Message):
    user_question = message.text
    response = await send_to_llm(user_question)
    
    await message.answer(response)

async def send_to_llm(question: str) -> str:
    url = "http://192.168.0.167:8000/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "/home/vapa/models/llms/qwen2.5-7b-instruct",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question}
        ],
        "max_tokens": 150  # Adjust as needed
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                result = await response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                return f"Error: Unable to get response from LLM server. Status code: {response.status}"

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
###