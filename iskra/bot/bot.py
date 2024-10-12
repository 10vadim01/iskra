import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

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
    return "Hello"
    # return response.choices[0].message['content']

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())