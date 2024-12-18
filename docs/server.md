Preffered OS for <span style="color:red">iskra-server</span> so far is `Ubuntu 22.04 LTS`.
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
Install poetry for python package management:
```sh
curl -sSL https://install.python-poetry.org | python3 -
```
If run into http error, try:
```sh
pip install 'urllib3<2.0'
```
Clone iskra repository:
```sh
git clone https://github.com/10vadim01/iskra.git
```
Install poetry dependencies:
```sh
poetry install
```


WSL2 setup:
Setup proxy and firewall rules on Windows and WSL2 for some service on port 2000:
```sh
netsh interface portproxy delete v4tov4 listenport=2000 listenaddress=192.168.0.161 (If there were any rules that broke connection)
netsh interface portproxy add v4tov4 listenport=2000 listenaddress=192.168.0.161 connectport=2000 connectaddress=172.28.15.200
```
Setup firewall rules for vLLM on port 2000:
```sh
$wslAddress = "172.28.15.200"

New-NetFirewallRule -DisplayName "vLLM" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 2000 -RemoteAddress Any
New-NetFirewallRule -DisplayName "vLLM Outbound" -Direction Outbound -Action Allow -Protocol TCP -RemotePort 2000 -RemoteAddress $wslAddress
```
Check proxies:
```sh
netsh interface portproxy show all
```
You should see something like this:
```
Listen on ipv4:             Connect to ipv4:
Address         Port        Address         Port
--------------- ----------  --------------- ----------
192.168.0.161   2000       172.28.15.200   2000
```
Allow connection in WSL2:
```sh
sudo ufw allow 2000
``` 
Test on Windows:
```sh
Test-NetConnection -ComputerName 172.28.15.200 -Port 2000
```

TTS:
Run TTS container:
```sh
sudo docker run --rm -it \
  -p 5002:5002 \
  --gpus all \
  -v /home/vapa/projects/iskra/data:/data \
  -v /home/vapa/projects/iskra/models/tts:/models \
  --entrypoint /bin/bash \
  ghcr.io/coqui-ai/tts
```

Download model:
```sh
wget https://huggingface.co/coqui/tts-models/resolve/main/tts_models--multilingual--multilingual-en--large-v2/model.tar.gz
unzip model.tar.gz
```

Run docker:
```sh
sudo docker run --rm -it \
  -p 5002:5002 \
  --gpus all \
  -v /home/vapa/Storage/:/data \
  -v /home/vapa/Storage/tts:/models \
  --entrypoint /bin/bash \
  ghcr.io/coqui-ai/tts
```

Run Jenny model inside of docker:
```sh
python3 /root/TTS/server/server.py --model_path="/models/jenny/model.pth" --config_path="/models/jenny/config.json" --use_cuda true --port 5002 
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
