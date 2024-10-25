from pvrecorder import PvRecorder
import pvporcupine
import os

PORCUPINE_ACCESS_KEY = os.getenv("ACCESS_KEY")
KEYWORD = "computer"

def wait_for_wake_word():
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
                break
                
    finally:
        if recorder is not None:
            recorder.delete()
        if porcupine is not None:
            porcupine.delete()
            
wait_for_wake_word()