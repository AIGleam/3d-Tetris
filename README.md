# AIGleam 3D Tetris

AIGleam 3D Tetris is a **free and open-source** futuristic take on the classic Tetris game, enhanced with immersive 3D graphics, neon aesthetics, and a dynamic soundtrack. This game is designed to challenge your spatial awareness with fully rotatable 3D tetrominoes!

[![Watch the Video](https://img.youtube.com/vi/s-O9TF1AN6c/maxresdefault.jpg)](https://youtu.be/s-O9TF1AN6c) 


## Features

- **True 3D Tetris Gameplay** – Rotate and drop pieces in a fully three-dimensional space.
- **Visuals** – Neon colors, grid-based effects, and immersive lighting.
- **Custom Soundtrack** – Dynamic background music that changes as you play.
- **Smooth OpenGL Rendering** – Powered by modern OpenGL for fluid performance.
- **Adaptive Camera Controls** – Zoom, rotate, and pan the game board for the perfect view.
- **High Score System** – Track and save your top performances.
- **Multiple Control Schemes** – Play with keyboard and mouse controls for the best experience.

## Controls

| Action | Key |
|--------|-----|
| Move Left/Right | `A` / `D` |
| Move Forward/Backward | `W` / `S` |
| Rotate Counterclockwise | `Q` |
| Rotate Clockwise | `E` |
| Rotate Z-axis | `R` |
| Drop Piece Instantly | `Space` |
| Pause | `P` |
| Zoom In/Out | Mouse Wheel |
| Rotate Camera | Left Click + Drag |
| Mute/Unmute Music | `M` |
| Increase Volume | `7` |
| Decrease Volume | `6` |
| Skip to Next Song | `8` |

## Installation

### Requirements

- Python 3.8+
- `pygame`
- `PyOpenGL`
- `numpy`

### Setup Instructions

##Download the Zip file with the Songs! Extract it to the directory your are running the Tetris.py from so you will have your song files! You can also replace it with your own song files if you'd like. just call the folder "Songs"

https://drive.google.com/file/d/1NZXmXL9KbZDC9LmXRLF2l9riOPmjoAfs/view?usp=sharing

#### Windows
1. **Install Python** from [python.org](https://www.python.org/downloads/) (Check *Add Python to PATH*).
2. **Install Git (Optional)** from [git-scm.com](https://git-scm.com/downloads).
3. **Clone the repository:**
   ```sh
   git clone https://github.com/AIGleam/3d-Tetris.git
   cd 3d-Tetris
   ```
4. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
5. **Run the game:**
   ```sh
   python main.py
   ```

#### macOS
1. **Install Homebrew** (if not installed):  
   ```sh
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. **Install Python & Git:**
   ```sh
   brew install python git
   ```
3. **Clone the repository:**
   ```sh
   git clone https://github.com/AIGleam/3d-Tetris.git
   cd 3d-Tetris
   ```
4. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
5. **Run the game:**
   ```sh
   python main.py
   ```

#### Linux (Ubuntu/Debian-based)
1. **Install dependencies:**
   ```sh
   sudo apt update && sudo apt install python3 python3-pip python3-venv git -y
   ```
2. **Clone the repository:**
   ```sh
   git clone https://github.com/AIGleam/3d-Tetris.git
   cd 3d-Tetris
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Run the game:**
   ```sh
   python main.py
   ```

### Troubleshooting
- **Linux/macOS:** If you get a *Permission Denied* error:  
  ```sh
  chmod +x main.py
  ```
- **OpenGL Issues:** Ensure graphics drivers are installed:  
  ```sh
  sudo apt install mesa-utils libgl1-mesa-glx libglu1-mesa -y  # Linux
  ```
  Windows users should update via NVIDIA/AMD/Intel's official site.

You're now ready to play **AIGleam 3D Tetris**! 🎮🚀


## Contributing

This project is open-source, and contributions are welcome! Feel free to fork the repository, submit issues, and create pull requests.

### How to Contribute
1. Fork the repository
2. Create a new branch (`git checkout -b feature-name`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to your branch (`git push origin feature-name`)
5. Open a Pull Request

## License

This project is licensed under the **MIT License**, meaning you are free to use, modify, and distribute it as you see fit.

## Follow Me for Updates

Stay connected and watch the latest developments on:

- 🎮 Twitch: [AIGleam](https://www.twitch.tv/aigleam)
- 🐦 Twitter: [@AIGleam](https://x.com/AIGleam)
- 📺 YouTube: [AIgleam](https://www.youtube.com/@AIgleam)
- 🌐 Website: [Keven.Ink](https://keven.ink) Want something fun/stupid built? Let me know! 

Happy gaming! 🎮🚀
