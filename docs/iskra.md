Preffered OS for <span style="color:orange">iskra</span> so far is `Ubuntu 22.04 LTS`.

Installed packages:
- `tmux`
- `git`
- `curl`
- `net-tools`
- `openssh-server`

Install with apt:
```sh
sudo apt install tmux git curl net-tools openssh-server
```
Install conda for python environment management:
```sh
wget https://repo.anaconda.com/archive/Anaconda3-2024.06-1-Linux-aarch64.sh
bash Anaconda3-2024.06-1-Linux-aarch64.sh
``` 
Create python environment for testing iskra :
```sh
conda create -n iskra python=3.10
conda activate iskra
```
Clone iskra repository:
```sh
git clone https://github.com/10vadim01/iskra.git
```
Install python dependencies (Not tested):
```sh
pip install -r iskra/requirements.txt
```
Install package in editable mode:
```sh
pip install -e .
```
Run some module:
```sh
python -m iskra.telegram.main
```
## Connect Speakers
Activate bluetoothctl:
```sh
sudo bluetoothctl
```
Set power on and make iskra discoverable:
```sh
power on
discoverable on
```
Pair and connect to iskra:
```sh
pair XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
```
Quit bluetoothctl:
```sh
quit
```

## Connect Microphone
Install alsa-utils:
```sh
sudo apt install alsa-utils
```
List available microphones:
```sh
arecord -l
```
Test recording:
```sh
arecord -d 5 test.wav
```
Play recording:
```sh
aplay test.wav
```

## Add-ons 

### Spotify Player
Use librespot to connect to spotify.
https://github.com/librespot-org/librespot/wiki/Options

install librespot
```sh
cargo install librespot
```

run librespot
```sh
librespot -n "iskra" -c .cache --device-type speaker --enable-oauth --oauth-port 0 
```

TTS:

Download model:
```sh
wget https://huggingface.co/coqui/tts-models/resolve/main/tts_models--multilingual--multilingual-en--large-v2/model.tar.gz
unzip model.tar.gz
```

Run docker:
```sh
sudo docker run --rm -it \
  -p 5000:5000 \
  --network host \
  --gpus all \
  -v /home/vapa/Storage/:/data \
  -v /home/vapa/Storage/tts:/models \
  --entrypoint /bin/bash \
  ghcr.io/coqui-ai/tts
```

Run Jenny model inside of docker:
```sh
python3 /root/TTS/server/server.py --model_path="/models/jenny/model.pth" --config_path="/models/jenny/config.json" --use_cuda true --port 5000 
```

Example of request:
```python
import requests
import tempfile
import subprocess

url = "http://192.168.0.161:5002/api/tts"
params = {"text": "Hello, this is a test"}

response = requests.post(url, params=params)

if response.status_code == 200:
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_audio:
        temp_audio.write(response.content)
        temp_audio.flush()
        subprocess.run(['aplay', temp_audio.name], check=True)
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

