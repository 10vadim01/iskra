from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from vllm import LLM, SamplingParams
import requests
import torch
import os

REMOTE_URL = "http://192.168.0.188:6996/play_song"

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


# Load ASR model
device = "cuda:0"

asr_model_id = "/home/vapa/projects/iskra/models/asr/whisper-large-v3"

asr_model = AutoModelForSpeechSeq2Seq.from_pretrained(
    asr_model_id, torch_dtype=torch.float16, use_safetensors=True
)
asr_model.to(device)

processor = AutoProcessor.from_pretrained(asr_model_id)

pipe = pipeline(
    "automatic-speech-recognition",
    model=asr_model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    torch_dtype=torch.float16,
    device=device,
)

# Load LLM model
llm_model_id = "/home/vapa/projects/iskra/models/llms/qwen2.5-7b-instruct"
llm = LLM(model=llm_model_id)

# FastAPI app
app = FastAPI()

UPLOAD_DIR = "/home/vapa/projects/iskra/data/recordings"

@app.post("/receive_audio")
async def receive_audio(audio: UploadFile = File(...)):
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    
    filename = "test.wav"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await audio.read())
        
    sample = "/home/vapa/projects/iskra/data/recordings/test.wav"
    result = pipe(sample)
    
    sampling_params = SamplingParams()
    response = llm.generate(spotify_prompt + "\n\n" + result["text"], sampling_params=sampling_params)
    request_output = response[0]
    generated_text = request_output.outputs[0].text
    with open("/home/vapa/projects/iskra/data/.txt", "w") as file:
        file.write(generated_text)
    response = requests.post(REMOTE_URL, json={"text": generated_text})
    
    return JSONResponse(content={"message": f"Audio file {filename} received and processed by LLM"}, status_code=200)

@app.get("/")
async def root():
    return {"message": "Audio receiver is ready"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
