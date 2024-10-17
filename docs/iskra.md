Preffered OS for <span style="color:orange">iskra</span> so far is `Ubuntu 22.04 LTS`.

Installed packages:
- `zsh`
- `tmux`
- `git`
- `vim`
- `curl`
- `net-tools`
- `openssh-server`

Install with apt:
```sh
sudo apt install zsh tmux git vim curl net-tools openssh-server
```
For easy shell navigation oh-my-zsh is installed:
```sh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```
Add plugins to zsh:
```sh
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
```
Add plugins to vim:
```sh
git clone https://github.com/preservim/nerdtree.git ~/.vim/pack/vendor/start/nerdtree
git clone https://github.com/vim-airline/vim-airline ~/.vim/pack/vendor/start/vim-airline
```
Install conda for python environment management:
```sh
wget https://repo.anaconda.com/archive/Anaconda3-2024.06-1-Linux-aarch64.sh
bash Anaconda3-2024.06-1-Linux-aarch64.sh
``` 

Install poetry for python package management:
```sh
curl -sSL https://install.python-poetry.org | python3 -
```
If run into http error, try:
```sh
pip install urllib3<2.0
```

## Add-ons 

### Spotify Player
Install rustup:
```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```
Install required dependencies:
```sh
sudo apt install libasound2-dev libssl-dev pkg-config build-essential
```
Clone repository:
```sh
git clone https://github.com/Spotifyd/spotifyd.git
```
Build spotifyd:
```sh
cd spotifyd
cargo build --release
```
Run spotifyd:
```sh
./target/release/spotifyd --no-daemon
```
Find iskra in Spotify client on another device and connect to it.

### Connect Speakers
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

### ExpressVPN 
(https://gist.github.com/martinbutt/a514621664dc17fcbd20d78f647bd14b)

Add armhf architecture (ExpressVPN is not available for arm64):
```sh
sudo dpkg --add-architecture armhf
sudo apt-get update
```
Install dependencies:
```sh
sudo apt install libc6:armhf
```
Install the cross compatibility libraries:
```sh
sudo apt-get install libc6-armhf-cross libstdc++6-armhf-cross patchelf
```
Link the interpreters to the expected locations:
```sh
sudo ln -s /usr/arm-linux-gnueabihf/lib/ld-linux-armhf.so.3  /lib/ld-linux-armhf.so.3
sudo ln -s /usr/arm-linux-gnueabihf/lib/ /lib/arm-linux-gnueabihf
```
Get the lastest version of the armhf (32-bit) package (labelled as Raspbian):
```sh
wget https://www.expressvpn.works/clients/linux/expressvpn_3.20.0.5-1_armhf.deb
```
Install as usual:
```sh
sudo dpkg -i expressvpn_3.20.0.5-1_armhf.deb
```
Patch the binaries to point to the armhf (32-bit) interpreter:
```sh
sudo patchelf --set-interpreter /lib/ld-linux-armhf.so.3 /usr/bin/expressvpn
sudo patchelf --set-interpreter /lib/ld-linux-armhf.so.3 /usr/bin/expressvpn-browser-helper
```
If error, try:
```sh
sudo apt --fix-broken install    
```
Start and activate the service:
```sh
sudo service expressvpn restart
expressvpn activate
expressvpn connect "Germany"
```
