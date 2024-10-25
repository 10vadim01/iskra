from pvrecorder import PvRecorder
import pvporcupine
import wave
import webrtcvad
import time
import os


vad = webrtcvad.Vad(3)  # Aggressiveness level 3 (most aggressive)
SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30
PADDING_DURATION_MS = 1000  # 1 sec of padding after last voice detection
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
MAX_DURATION = 10  # Maximum recording duration in seconds

DURATION = 5

PORCUPINE_ACCESS_KEY = os.getenv("ACCESS_KEY")
KEYWORD = "computer"

# At the top with other constants
FRAME_LENGTH = 480  # 30ms at 16kHz

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
                    record_with_vad()
                    
                    
        except Exception as e:
            print(f"Error in wake word listener: {e}")
        finally:
            if 'recorder' in locals() and recorder is not None:
                recorder.delete()
            if 'porcupine' in locals() and porcupine is not None:
                porcupine.delete()

    
def record_with_vad():
    print("Recording... Speak now!")
    output_filename = "test.wav"
    
    recorder = PvRecorder(device_index=-1, frame_length=FRAME_LENGTH)
    recorder.start()
    
    frames = []
    silent_frames = 0
    max_silent_frames = int(PADDING_DURATION_MS / FRAME_DURATION_MS)
    start_time = time.time()
    
    try:
        while True:
            frame = recorder.read()
            
            # Convert int16 values to bytes for VAD
            frame_bytes = b''
            for sample in frame:
                sample = max(-32768, min(32767, int(sample)))
                frame_bytes += sample.to_bytes(2, byteorder='little', signed=True)
            
            # Check if the frame is valid for VAD
            if len(frame_bytes) == FRAME_LENGTH * 2:  # multiply by 2 because each sample is 2 bytes
                is_speech = vad.is_speech(frame_bytes, SAMPLE_RATE)
                frames.append(frame)
                
                if is_speech:
                    silent_frames = 0
                else:
                    silent_frames += 1
                
                # Stop conditions
                if silent_frames > max_silent_frames:
                    print("Speaking stopped")
                    break
                if time.time() - start_time > MAX_DURATION:
                    print("Maximum duration reached")
                    break
            
    finally:
        recorder.stop()
        recorder.delete()
    
    # Write frames to WAV file
    with wave.open(output_filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        audio_data = b''
        for frame in frames:
            for sample in frame:
                sample = max(-32768, min(32767, int(sample)))
                audio_data += sample.to_bytes(2, byteorder='little', signed=True)
        wav_file.writeframes(audio_data)
    
    return output_filename

def main():
    try:
        # Wait for wake word
        wake_word_listener()
        
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
