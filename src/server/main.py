from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import requests
import torch
import os

REMOTE_URL = "http://192.168.0.188:6996/"

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
    result = pipe(sample, generate_kwargs={"language": "english"})
    
    with open("/home/vapa/projects/iskra/data/asr/play/request.txt", "w") as file:
        file.write(result["text"])
    
    payload = {
        "model": "/home/vapa/projects/iskra/models/llms/vikhr-12b",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant iskra, help users by answering their questions and entertaining them."},
            {"role": "user", "content": result["text"]} 
        ]
    }
    
    response = requests.post("http://0.0.0.0:8000/v1/chat/completions", json=payload)
    generated_text = response.json()["choices"][0]["message"]["content"]
    
    special_commands = ["<sp_song>", "<sp_stop>", "<sp_next>", "<sp_continue>", "<sp_previous>"]
    is_special_command = any(cmd in generated_text for cmd in special_commands)
    
    with open("/home/vapa/projects/iskra/data/llms/play/response.txt", "w") as file:
        file.write(generated_text)
    
    if is_special_command:
        response = requests.post(f"{REMOTE_URL}/play_song", json={"text": generated_text})
    
    else:
        response = requests.post(f"{REMOTE_URL}/talk", json={"text": generated_text})
        
    # else:
    #     url = "http://localhost:5002/api/tts"
    #     headers = {"text": generated_text}
    #     response = requests.post(url, headers=headers)

    #     with open("/home/vapa/projects/iskra/data/tts/responses/output.wav", "wb") as f:
    #         f.write(response.content)
        
    #     with open("/home/vapa/projects/iskra/data/tts/responses/output.wav", "rb") as f:
    #         files = {"audio": f}
    #         response = requests.post(f"{REMOTE_URL}/talk", files=files)
    
    return JSONResponse(content={"message": f"Audio file {filename} received and processed by LLM"}, status_code=200)

@app.get("/")
async def root():
    return {"message": "Audio receiver is ready"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
