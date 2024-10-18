import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from iskra.modules.spotify import play_track, continue_track, stop_track, play_next_track, play_previous_track
import aiohttp
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

token = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=token)
dp = Dispatcher()

spotify_functions = {
    "play_track": play_track,
    "continue_track": continue_track,
    "stop_track": stop_track,
    "play_next_track": play_next_track,
    "play_previous_track": play_previous_track
}

spotify_prompt = """
You have access to a Spotify player. If a user asks you to perform an action with the music player (play a track, stop playing, play next track, play previous track), include the appropriate function call in your response using the following format:

[FUNCTION_CALL]function_name(argument)[/FUNCTION_CALL]

Available functions:
- play_track(track_name: str)
- stop_track()
- play_next_track()
- play_previous_track()

Example: To play a track, include [FUNCTION_CALL]play_track(Bohemian Rhapsody)[/FUNCTION_CALL] in your response.
"""


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hello!")

@dp.message()
async def handle_user_message(message: types.Message):
    user_question = message.text
    response = await send_to_llm(user_question)
    
    logger.info(f"LLM response: {response}")
    
    function_calls = re.findall(r'\[FUNCTION_CALL\](.*?)\[/FUNCTION_CALL\]', response)
    
    for func_call in function_calls:
        func_name, _, argument = func_call.partition('(')
        argument = argument.rstrip(')')
        
        if func_name in spotify_functions:
            func = spotify_functions[func_name]
            logger.info(f"Attempting to call {func_name} with argument: {argument}")
            try:
                if argument:
                    spotify_response = await func(argument)
                else:
                    spotify_response = await func()
                logger.info(f"Spotify response: {spotify_response}")
                response = response.replace(f"[FUNCTION_CALL]{func_call}[/FUNCTION_CALL]", spotify_response)
            except Exception as e:
                error_message = f"Error executing {func_name}: {str(e)}"
                logger.error(error_message)
                response = response.replace(f"[FUNCTION_CALL]{func_call}[/FUNCTION_CALL]", error_message)
    
    response = re.sub(r'\[FUNCTION_CALL\].*?\[/FUNCTION_CALL\]', '', response)
    
    await message.answer(response.strip())

async def send_to_llm(question: str) -> str:
    url = "http://192.168.0.167:8000/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "/home/vapa/projects/iskra/models/llms/qwen2.5-7b-instruct",
        "messages": [
            {"role": "system", "content": f"You are a helpful assistant. {spotify_prompt}"},
            {"role": "user", "content": question}
        ],
        "max_tokens": 8192
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
