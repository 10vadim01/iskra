from faster_whisper import WhisperModel, BatchedInferencePipeline
import speech_recognition as sr
import tempfile
import requests
import os

model_size = "large-v3"
model = WhisperModel(model_size, device="cuda", compute_type="float16")
batched_model = BatchedInferencePipeline(model=model)


def recognize_with_whisper():
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1.5
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)
        
        while True:
            try:
                audio = recognizer.listen(source)
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                    wav_data = audio.get_wav_data()
                    temp_audio.write(wav_data)
                    temp_audio_path = temp_audio.name

                try:
                    segments, info = batched_model.transcribe(temp_audio_path, batch_size=16, language="en")
                    for segment in segments:
                        payload = {
                            "model": "/home/vapa/Storage/llms/iskra-7b-player",
                            "messages": [
                                {"role": "system", "content": "You are a helpful assistant iskra, help users by answering their questions and entertaining them."},
                                {"role": "user", "content": segment.text}
                            ]
                        }
                        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
                        response = requests.post("http://0.0.0.0:8000/v1/chat/completions", json=payload)
                        generated_text = response.json()["choices"][0]["message"]["content"]
                        print(generated_text)
                finally:
                    os.unlink(temp_audio_path)
                
            except sr.UnknownValueError:
                print("Could not understand audio")
            except KeyboardInterrupt:
                print("Stopping...")
                break

if __name__ == "__main__":
    recognize_with_whisper()