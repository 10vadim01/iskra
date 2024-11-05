from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from client.modules.spotify import search_and_play_track
from pvrecorder import PvRecorder
from threading import Thread
import pvporcupine
import subprocess
import requests
import tempfile
import uvicorn
import os

app = FastAPI()

REMOTE_URL = "http://192.168.0.161:3000/receive_audio"
DURATION = 5

PORCUPINE_ACCESS_KEY = os.getenv("ACCESS_KEY")
KEYWORD = "computer"

def wake_word_listener():
    while True:
        try:
            porcupine = pvporcupine.create(
                access_key=PORCUPINE_ACCESS_KEY,
                keywords=[KEYWORD]
            )
            recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
            recorder.start()
            
            print(f"Listening for wake word '{KEYWORD}'...")
            
            while True:
                pcm = recorder.read()
                result = porcupine.process(pcm)
                if result >= 0:
                    print("Wake word detected!")
                    requests.post("http://localhost:6996/record")
                    
        except Exception as e:
            print(f"Error in wake word listener: {e}")
        finally:
            if 'recorder' in locals() and recorder is not None:
                recorder.delete()
            if 'porcupine' in locals() and porcupine is not None:
                porcupine.delete()

def record_and_send():
    with tempfile.TemporaryDirectory() as temp_dir:
        filename = os.path.join(temp_dir, "audio.wav")
        try:
            result = subprocess.run(
                ["arecord", "-d", str(DURATION), "-r", "16000", "-f", "S16_LE", filename],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"Audio recording completed: {result.stdout}")
        except subprocess.CalledProcessError as e:
            error_message = f"Audio recording failed: {e.stderr}"
            print(error_message)
            raise HTTPException(status_code=500, detail=error_message)

        if not os.path.exists(filename):
            error_message = f"Audio file {filename} was not created"
            print(error_message)
            raise HTTPException(status_code=500, detail=error_message)

        try:
            audio_file = open(filename, "rb")
            files = {"audio": (filename, audio_file, "audio/wav")}
            response = requests.post(REMOTE_URL, files=files)
            print(f"Sent {filename}, response: {response.status_code}")
            return response.status_code
        except Exception as e:
            error_message = f"Error processing or sending audio: {str(e)}"
            print(error_message)
            raise HTTPException(status_code=500, detail=error_message)
        finally:
            audio_file.close()

@app.post("/record")
async def record_audio(background_tasks: BackgroundTasks):
    background_tasks.add_task(record_and_send)
    return {"message": "Audio recording and sending started"}

@app.post("/play_song")
async def play_song(request: Request):
    data = await request.json()
    text = data.get("text", "")
    print(f"Playing song: {text}")
    return await search_and_play_track(text)

@app.get("/")
async def root():
    return {"message": "Audio sender is ready"}

if __name__ == "__main__":
    wake_thread = Thread(target=wake_word_listener, daemon=True)
    wake_thread.start()
    
    uvicorn.run(app, host="0.0.0.0", port=6996)
