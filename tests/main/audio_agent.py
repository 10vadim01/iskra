from faster_whisper import WhisperModel, BatchedInferencePipeline
import speech_recognition as sr
import subprocess
import tempfile
import requests
import logging
import json
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AudioAgent:
    def __init__(self):
        self.tts_host = "http://127.0.0.1:5000" 
        self.llm_host = "http://127.0.0.1:8000"
        self.llm_model = "/home/vapa/Storage/llms/iskra-7b-player"
        self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        self.batched_model = BatchedInferencePipeline(model=self.whisper_model)
        self.recognizer = self._setup_recognizer()
        self._test_connections()

    def _setup_recognizer(self):
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 1
        return recognizer

    def _setup_microphone(self, source):
        logger.info("Adjusting for ambient noise...")
        self.recognizer.adjust_for_ambient_noise(source, duration=2)
        logger.info("Ready to listen!")

    def _save_audio_to_temp(self, audio_data):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(audio_data.get_wav_data())
            logger.info(f"Audio saved to temporary file: {temp_audio.name}")
            return temp_audio.name

    def _transcribe_audio(self, audio_path):
        segments, _ = self.batched_model.transcribe(audio_path, batch_size=16, language="en")
        return segments

    def _create_llm_payload(self, text):
        return {
            "model": self.llm_model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant iskra, help users by answering their questions and entertaining them."},
                {"role": "user", "content": text}
            ],
            "stream": True
        }

    def _play_audio_chunk(self, audio_content):
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_audio:
            temp_audio.write(audio_content)
            temp_audio.flush()
            subprocess.run(['aplay', temp_audio.name], check=True)

    def _process_tts(self, text):
        try:
            tts_response = requests.post(
                f"{self.tts_host}/api/tts",
                params={"text": text},
                timeout=10
            )
            if tts_response.status_code == 200:
                logger.info("TTS request successful")
                self._play_audio_chunk(tts_response.content)
                return True
            logger.error(f"TTS request failed with status code: {tts_response.status_code}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"TTS request failed: {e}")
            return False

    def _process_llm_response(self, response):
        text_buffer = ""
        for line in response.iter_lines():
            if not line:
                continue

            try:
                line_text = line.decode('utf-8')
                if line_text == "data: [DONE]":
                    if text_buffer:
                        logger.info(f"Processing final text buffer: {text_buffer}")
                        self._process_tts(text_buffer)
                    break

                if line_text.startswith('data: '):
                    text_buffer = self._handle_llm_data(line_text[6:], text_buffer)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")

    def _handle_llm_data(self, json_str, text_buffer):
        if not json_str.strip():
            return text_buffer

        json_response = json.loads(json_str)
        if 'choices' not in json_response:
            return text_buffer

        delta = json_response['choices'][0].get('delta', {})
        if 'content' not in delta:
            return text_buffer

        content = delta['content']
        print(content, end='', flush=True)
        text_buffer += content

        if any(punct in content for punct in '.!?:'):
            logger.info(f"Processing text buffer at punctuation: {text_buffer}")
            if self._process_tts(text_buffer):
                return ""
        return text_buffer

    def _test_connections(self):
        logger.info("Testing server connections...")
        services_ok = True
        
        try:
            tts_response = requests.post(
                f"{self.tts_host}/api/tts",
                params={"text": "Connection test"},
                timeout=5
            )
            logger.info(f"TTS server test - Status: {tts_response.status_code}")
            if tts_response.status_code != 200:
                logger.error(f"TTS server error: {tts_response.text}")
                services_ok = False
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to TTS server: {e}")
            services_ok = False

        try:
            test_payload = self._create_llm_payload("Connection test")
            llm_response = requests.post(
                f"{self.llm_host}/v1/chat/completions",
                json=test_payload,
                timeout=5
            )
            logger.info(f"LLM server test - Status: {llm_response.status_code}")
            if llm_response.status_code != 200:
                logger.error(f"LLM server error: {llm_response.text}")
                services_ok = False
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to LLM server: {e}")
            services_ok = False

        if not services_ok:
            raise RuntimeError("Failed to connect to required services. Please check the logs and ensure all services are running.")

    def process_audio_stream(self):
        logger.info("Initializing speech recognition")
        
        with sr.Microphone() as source:
            self._setup_microphone(source)
            
            while True:
                try:
                    logger.info("Listening for speech...")
                    audio = self.recognizer.listen(source)
                    temp_audio_path = self._save_audio_to_temp(audio)

                    try:
                        segments = self._transcribe_audio(temp_audio_path)
                        for segment in segments:
                            logger.info(f"Transcribed text: {segment.text}")
                            
                            logger.info("Sending request to LLM...")
                            payload = self._create_llm_payload(segment.text)
                            response = requests.post(f"{self.llm_host}/v1/chat/completions", json=payload, stream=True)
                            self._process_llm_response(response)
                                            
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

def main():
    processor = AudioAgent()
    processor.process_audio_stream()

if __name__ == "__main__":
    main()