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