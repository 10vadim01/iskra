from fastapi import FastAPI, BackgroundTasks, Request
from fastapi import HTTPException
import subprocess
import requests
import tempfile
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = FastAPI()

scope = "user-read-playback-state,user-modify-playback-state"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

REMOTE_URL = "http://192.168.0.161:3000/receive_audio"
DURATION = 5

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
    try:
        results = sp.search(q=f'track:{text}', type='track', limit=1)
        tracks = results['tracks']['items']
        
        if tracks:
            track = tracks[0]
            track_id = f"spotify:track:{track['id']}"
            sp.start_playback(uris=[track_id])
            return f"Message from Spotify: Found '{track['name']}' by {track['artists'][0]['name']}"
        else:
            return f"Message from Spotify: No '{text}' was found on Spotify."
    except Exception as e:
        return f"Message from Spotify: An error occurred while trying to play the track: {str(e)}"

@app.get("/")
async def root():
    return {"message": "Audio sender is ready"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6996)
