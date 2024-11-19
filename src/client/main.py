from fastapi import FastAPI, BackgroundTasks, HTTPException
from client.modules.spotify import search_and_play_track, stop_track, play_next_track, play_previous_track
from pvrecorder import PvRecorder
from threading import Thread
import pvporcupine
import requests
import tempfile
import uvicorn
import os
import wave
import webrtcvad
import time
import subprocess
from pyht import Client
from pyht.client import TTSOptions, Language

app = FastAPI()

REMOTE_URL = "http://192.168.0.161:3000/receive_audio"

PORCUPINE_ACCESS_KEY = os.getenv("ACCESS_KEY")
KEYWORD = "computer"

vad = webrtcvad.Vad(3)
FRAME_LENGTH = 480
FRAME_DURATION_MS = 30
PADDING_DURATION_MS = 2000
MAX_DURATION = 10

play_ht_client = Client(
    user_id=os.getenv("PLAY_HT_USER_ID"),
    api_key=os.getenv("PLAY_HT_API_KEY"),
)
play_ht_options = TTSOptions(
    voice="s3://voice-cloning-zero-shot/775ae416-49bb-4fb6-bd45-740f205d20a1/jennifersaad/manifest.json",
    speed=1.0,
    language=Language.ENGLISH
)

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
                    os.system("amixer -D pulse sset Master 0%")
                    requests.post("http://localhost:6996/record")
                    
                    
        except Exception as e:
            print(f"Error in wake word listener: {e}")
        finally:
            if 'recorder' in locals() and recorder is not None:
                recorder.delete()
            if 'porcupine' in locals() and porcupine is not None:
                porcupine.delete()

async def record_and_send():
    with tempfile.TemporaryDirectory() as temp_dir:
        output_filename = os.path.join(temp_dir, "audio.wav")
        print(f"Created temporary file: {output_filename}")
        
        recorder = PvRecorder(device_index=-1, frame_length=FRAME_LENGTH)
        recorder.start()
        
        frames = []
        silent_frames = 0
        max_silent_frames = int(PADDING_DURATION_MS / FRAME_DURATION_MS)
        start_time = time.time()
        
        try:
            print("Recording... Speak now!")
            while True:
                frame = recorder.read()
                
                frame_bytes = b''
                for sample in frame:
                    sample = max(-32768, min(32767, int(sample)))
                    frame_bytes += sample.to_bytes(2, byteorder='little', signed=True)
                
                if len(frame_bytes) == FRAME_LENGTH * 2:
                    is_speech = vad.is_speech(frame_bytes, 16000)
                    frames.append(frame)
                    
                    if is_speech:
                        silent_frames = 0
                    else:
                        silent_frames += 1
                    
                    if silent_frames > max_silent_frames:
                        print("Speaking stopped")
                        break
                    if time.time() - start_time > MAX_DURATION:
                        print("Maximum duration reached")
                        break
                
        finally:
            recorder.stop()
            recorder.delete()
        
        with wave.open(output_filename, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            audio_data = b''
            for frame in frames:
                for sample in frame:
                    sample = max(-32768, min(32767, int(sample)))
                    audio_data += sample.to_bytes(2, byteorder='little', signed=True)
            wav_file.writeframes(audio_data)

        try:
            audio_file = open(output_filename, "rb")
            files = {
                "file": ("audio.wav", audio_file, "audio/wav")
            }
            data = {
                "temperature": "0.2",
                "response-format": "json",
                "audio_format": "wav"
            }
            
            inference_url = "http://127.0.0.1:8080/inference"
            print(f"Sending request to {inference_url}")
            response = requests.post(inference_url, files=files, data=data)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_json = response.json()
                    transcribed_text = response_json.get("text", "")
                    with open(f"/var/log/iskra/asr/response-{time.time()}.txt", "w") as file:
                        file.write(transcribed_text)
                    print(f"Transcribed text: {transcribed_text}")
                    
                    payload = {
                        "model": "/home/vapa/Storage/llms/iskra-7b-player",
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant. Answer the user's question and play music if needed."},
                            {"role": "user", "content": transcribed_text} 
                        ]
                    }
                    
                    response = requests.post("http://192.168.0.161:8000/v1/chat/completions", json=payload)
                    generated_text = response.json()["choices"][0]["message"]["content"]
                    
                    with open(f"/var/log/iskra/llm/response-{time.time()}.txt", "w") as file:
                        file.write(generated_text)
                    
                    special_commands = ["<sp_song>", "<sp_stop>", "<sp_next>", "<sp_continue>", "<sp_previous>"]
                    is_special_command = any(cmd in generated_text for cmd in special_commands)
                    
                    if is_special_command:
                        command = generated_text.strip()
                        print(f"Spotify command: {command}")
                        os.system("amixer -D pulse sset Master 40%")

                        if command in ["<sp_stop>", "<sp_next>", "<sp_previous>"]:
                            command_map = {
                                "<sp_stop>": stop_track,
                                "<sp_next>": play_next_track,
                                "<sp_previous>": play_previous_track
                            }
                            await command_map[command]()
                            return {"message": "Spotify command executed"}

                        if command.startswith("<sp_song>"):
                            query = command[8:].strip()
                            print(f"Searching for: {query}")
                            await search_and_play_track(query)
                            return {"message": "Playing song"}

                    else:
                        try:
                            temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                            try:
                                for chunk in play_ht_client.tts(generated_text, play_ht_options):
                                    temp_audio.write(chunk)
                                temp_audio.flush()
                                temp_audio_path = temp_audio.name
                                temp_audio.close()
                                
                                stop_track()
                                os.system("amixer -D pulse sset Master 40%")
                                subprocess.run(['aplay', temp_audio_path], check=True)
                                os.unlink(temp_audio_path)
                                
                                return {"message": "Audio played successfully"}
                            except Exception as e:
                                if not temp_audio.closed:
                                    temp_audio.close()
                                if os.path.exists(temp_audio.name):
                                    os.unlink(temp_audio.name)
                                raise HTTPException(status_code=500, detail=f"Error playing audio: {str(e)}")
                        except Exception as e:
                            raise HTTPException(status_code=500, detail=f"Error creating temporary file: {str(e)}")
                    

                except ValueError as e:
                    print(f"Error parsing JSON response: {e}")
                    raise HTTPException(status_code=500, detail="Invalid response format")
            else:
                raise HTTPException(status_code=response.status_code, detail="Inference request failed")
                
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
    

@app.get("/")
async def root():
    return {"message": "Audio sender is ready"}

if __name__ == "__main__":
    wake_thread = Thread(target=wake_word_listener, daemon=True)
    wake_thread.start()
    
    uvicorn.run(app, host="0.0.0.0", port=6996)
