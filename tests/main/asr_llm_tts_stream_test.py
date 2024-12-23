from faster_whisper import WhisperModel, BatchedInferencePipeline
import speech_recognition as sr
import subprocess
import tempfile
import requests
import json
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TTS_HOST = "http://0.0.0.0:5000"
logger.info(f"Using TTS server at: {TTS_HOST}")

model_size = "base"
model = WhisperModel(model_size, device="cpu", compute_type="int8")
batched_model = BatchedInferencePipeline(model=model)


def recognize_with_whisper():
    logger.info("Initializing speech recognition")
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1
    
    with sr.Microphone() as source:
        logger.info("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        logger.info("Ready to listen!")
        
        while True:
            try:
                logger.info("Listening for speech...")
                audio = recognizer.listen(source)
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                    wav_data = audio.get_wav_data()
                    temp_audio.write(wav_data)
                    temp_audio_path = temp_audio.name
                    logger.info(f"Audio saved to temporary file: {temp_audio_path}")

                try:
                    segments, info = batched_model.transcribe(temp_audio_path, batch_size=16, language="en")
                    for segment in segments:
                        logger.info(f"Transcribed text: {segment.text}")
                        
                        logger.info("Sending request to LLM...")
                        payload = {
                            "model": "/home/vapa/Storage/llms/iskra-7b-player",
                            "messages": [
                                {"role": "system", "content": "You are a helpful assistant iskra, help users by answering their questions and entertaining them."},
                                {"role": "user", "content": segment.text}
                            ],
                            "stream": True
                        }
                        response = requests.post("http://0.0.0.0:8000/v1/chat/completions", json=payload, stream=True)
                        text_buffer = ""

                        for line in response.iter_lines():
                            if line:
                                try:
                                    line_text = line.decode('utf-8')
                                    if line_text == "data: [DONE]":
                                        if text_buffer:
                                            logger.info(f"Processing final text buffer: {text_buffer}")
                                            logger.info("Sending final chunk to TTS...")
                                            tts_response = requests.post(
                                                "http://localhost:5002/api/tts",
                                                params={"text": text_buffer}
                                            )
                                            if tts_response.status_code == 200:
                                                logger.info("Playing final audio chunk")
                                                with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_audio:
                                                    temp_audio.write(tts_response.content)
                                                    temp_audio.flush()
                                                    subprocess.run(['aplay', temp_audio.name], check=True)
                                        break
                                    
                                    if line_text.startswith('data: '):
                                        json_str = line_text[6:]
                                        if json_str.strip():
                                            json_response = json.loads(json_str)
                                            if 'choices' in json_response:
                                                delta = json_response['choices'][0].get('delta', {})
                                                if 'content' in delta:
                                                    content = delta['content']
                                                    print(content, end='', flush=True)
                                                    text_buffer += content
                                                    if any(punct in content for punct in '.!?,:'):
                                                        logger.info(f"Processing text buffer at punctuation: {text_buffer}")
                                                        logger.info("Sending chunk to TTS...")
                                                        try:
                                                            tts_response = requests.post(
                                                                f"{TTS_HOST}/api/tts",
                                                                params={"text": text_buffer},
                                                                timeout=10
                                                            )
                                                            if tts_response.status_code == 200:
                                                                logger.info("TTS request successful")
                                                                with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_audio:
                                                                    temp_audio.write(tts_response.content)
                                                                    temp_audio.flush()
                                                                    subprocess.run(['aplay', temp_audio.name], check=True)
                                                                text_buffer = ""
                                                            else:
                                                                logger.error(f"TTS request failed with status code: {tts_response.status_code}")
                                                        except requests.exceptions.RequestException as e:
                                                            logger.error(f"TTS request failed: {e}")
                                except json.JSONDecodeError as e:
                                    logger.error(f"JSON decode error: {e}")
                                    continue
                                            
                except Exception as e:
                    logger.error(f"Error during transcription or processing: {e}")
                finally:
                    logger.info(f"Cleaning up temporary file: {temp_audio_path}")
                    os.unlink(temp_audio_path)
                
            except sr.UnknownValueError:
                logger.warning("Could not understand audio")
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, stopping...")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    recognize_with_whisper()