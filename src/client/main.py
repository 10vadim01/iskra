from fastapi import FastAPI, BackgroundTasks, Request, HTTPException, File, UploadFile
from client.modules.spotify import search_and_play_track, stop_track, play_next_track, play_previous_track
from pvrecorder import PvRecorder
from threading import Thread
import pvporcupine

import wave
import webrtcvad
import time
import subprocess


app = FastAPI()

REMOTE_URL = "http://192.168.0.161:3000/receive_audio"

PORCUPINE_ACCESS_KEY = os.getenv("ACCESS_KEY")
KEYWORD = "computer"


vad = webrtcvad.Vad(3)
FRAME_LENGTH = 480
FRAME_DURATION_MS = 30
PADDING_DURATION_MS = 2000
MAX_DURATION = 10

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
                    # record_and_send()
                    
                    
        except Exception as e:
            print(f"Error in wake word listener: {e}")
        finally:
            if 'recorder' in locals() and recorder is not None:
                recorder.delete()
            if 'porcupine' in locals() and porcupine is not None:
                porcupine.delete()

def record_and_send():
    with tempfile.TemporaryDirectory() as temp_dir:
        output_filename = os.path.join(temp_dir, "audio.wav")
        
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
            files = {"audio": (output_filename, audio_file, "audio/wav")}
            response = requests.post(REMOTE_URL, files=files)
            print(f"Sent {output_filename}, response: {response.status_code}")
            
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
    command = data.get("text", "").lower().strip()
    print(f"Spotify command: {command}")
    os.system("amixer -D pulse sset Master 30%")
    
    if command in ["<sp_stop>", "<sp_next>", "<sp_previous>"]:
        command_map = {
            "<sp_stop>": stop_track,
            "<sp_next>": play_next_track,
            "<sp_previous>": play_previous_track
        }
        return await command_map[command]()
    
    if command.startswith("<sp_song>"):
        query = command[8:].strip()
        print(f"Searching for: {query}")
        return await search_and_play_track(query)
    
    return await search_and_play_track(command)


@app.get("/")
async def root():
    return {"message": "Audio sender is ready"}

@app.post("/talk")
async def play_audio(audio: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            temp_audio.write(await audio.read())
            temp_audio.flush()
            stop_track()
            
            os.system("amixer -D pulse sset Master 30%")
            subprocess.run(['aplay', temp_audio.name], check=True)
            os.unlink(temp_audio.name)
            
        return {"message": "Audio played successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error playing audio: {str(e)}")


if __name__ == "__main__":
    wake_thread = Thread(target=wake_word_listener, daemon=True)
    wake_thread.start()
    
    uvicorn.run(app, host="0.0.0.0", port=6996)
