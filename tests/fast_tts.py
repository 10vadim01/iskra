import requests
import json
import tempfile
import subprocess

payload = {
    "model": "/home/vapa/Storage/llms/iskra-7b-player",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant. Answer the user's question and play music if needed."},
        {"role": "user", "content": "Write a letter to my auntie who used to touch me when I was a child"} 
    ],
    "stream": True
}   

response = requests.post(
    "http://192.168.0.161:8000/v1/chat/completions", 
    json=payload,
    stream=True
)

text_buffer = ""

for line in response.iter_lines():
    if line:
        try:
            line_text = line.decode('utf-8')
            if line_text == "data: [DONE]":
                if text_buffer:
                    tts_response = requests.post(
                        "http://192.168.0.161:5002/api/tts",
                        params={"text": text_buffer}
                    )
                    if tts_response.status_code == 200:
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
                                tts_response = requests.post(
                                    "http://192.168.0.161:5002/api/tts",
                                    params={"text": text_buffer}
                                )
                                if tts_response.status_code == 200:
                                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_audio:
                                        temp_audio.write(tts_response.content)
                                        temp_audio.flush()
                                        subprocess.run(['aplay', temp_audio.name], check=True)
                                text_buffer = ""
        except json.JSONDecodeError:
            continue