from pyht import Client
from pyht.client import TTSOptions, Language
import os
import tempfile
import subprocess

client = Client(
    user_id=os.getenv("PLAY_HT_USER_ID"),
    api_key=os.getenv("PLAY_HT_API_KEY"),
)
options = TTSOptions(
    voice="s3://voice-cloning-zero-shot/775ae416-49bb-4fb6-bd45-740f205d20a1/jennifersaad/manifest.json",
    speed=1.0,
    language=Language.ENGLISH
)


prompt = """I guess this API is ass and I am switching to local TTS"""

with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_audio:
    for chunk in client.tts(prompt, options):
        temp_audio.write(chunk)
    
    temp_audio.flush()
    
    subprocess.run(['aplay', temp_audio.name], check=True)