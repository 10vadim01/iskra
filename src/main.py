from audio_agent import AudioAgent
from pathlib import Path
from typing import Dict
import argparse
import yaml

def load_config(config_path: str) -> Dict:
    default_config_path = Path(__file__).parent.parent / 'configs' / 'default.yaml'
    with open(default_config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    with open(config_path, 'r') as f:
        user_config = yaml.safe_load(f)
    
    def deep_update(base_dict, update_dict):
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict:
                deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    deep_update(config, user_config)
    return config

def main():
    parser = argparse.ArgumentParser(description='Run Audio Agent with configuration')
    parser.add_argument('--config', '-c', 
                       default='configs/default.yaml',
                       help='Path to configuration file')
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        agent = AudioAgent(
            llm_host=config['LLM']['host'],
            llm_model=config['LLM']['model_path'],
            system_prompt=config['LLM']['system_prompt'],
            tts_host=config['TTS']['host'],
            asr_model=config['ASR']['model'],
            asr_device=config['ASR']['device'],
            asr_compute_type=config['ASR']['compute_type']
        )
        agent.process_audio_stream()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
