# Street Fighter Game

A 2D fighting game inspired by the classic Street Fighter series, built with Python and Pygame. I developed this as a solo project for my class at IEK AKMH, a Greek private school, to showcase my skills in game development, sprite animation, AI programming, and creating user interfaces.

## 🎮 Overview

This Street Fighter clone includes two game modes: playing against an AI opponent or battling a friend locally. Fighters have various animations like standing idle, walking, jumping, attacking, taking damage, and blocking. The game features round-based fights with health bars, collision detection, and different backgrounds for each mode.

**Time spent:** About 50 hours total, including finding and integrating assets, coding everything, debugging, and writing documentation.

## ✨ Features

- **Game Modes:**
  - Single-player: Fight against a computer-controlled opponent
  - Multi-player: Local 2-player combat

- **Fighter Abilities:**
  - Movement: Walk left/right, jump
  - Combat: Attack, defend with shield
  - Health system with visible health bars
  - Collision detection and knockback effects

- **Visuals:**
  - Animated sprites for all fighter actions
  - Different backgrounds for single-player and multi-player
  - Modern UI with custom buttons and menus
  - Smooth animations throughout

- **Game Flow:**
  - Round-based matches
  - Win/lose conditions
  - End-game menu with options to restart or go back

## 🛠️ Requirements

- Python 3.6 or higher
- Pygame library

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/street-fighter-game.git
   cd street-fighter-game
   ```

2. **Install dependencies:**
   ```bash
   pip install pygame
   ```

3. **Run the game:**
   ```bash
   python street_fighter.py
   ```

## 🎯 Controls

### Player 1 (Left Side)
- **A/D:** Move left/right
- **W:** Jump
- **S:** Shield
- **Space:** Attack

### Player 2 (Right Side) - Multiplayer Mode
- **Left/Right Arrow:** Move left/right
- **Up Arrow:** Jump
- **Down Arrow:** Shield
- **Enter:** Attack

### Menu Navigation
- **Mouse:** Click buttons to select options
- **Hover effects:** Buttons light up when you hover over them

## 📁 Project Structure

```
PYTHON/
├── street_fighter.py      # Main game file
├── constants.py           # Game constants and colors
├── fighter.py             # Fighter class with mechanics
├── menu.py                # Menu system
├── round_manager.py       # Round logic and scoring
├── cpu_controller.py      # AI opponent logic
├── sprite_loader.py       # Sprite animation handler
└── assets/
    ├── backgrounds/       # Background images
    ├── buttons/           # UI button images
    └── sprites/           # Fighter sprites (player1, player2, cpu)
        ├── player1/       # Player 1 animations
        ├── player2/       # Player 2 animations
        └── cpu/           # CPU opponent animations
```

## 🎨 Assets

I used a mix of assets for the visuals:
- **AI-generated:** The UI buttons and the main menu background image
- **Free online assets:** All the fighter sprites (for idle, walking, jumping, attacking, getting hurt, dying, and shielding) plus the background images for the different game modes

## 🚀 How to Play

1. Start the game
2. Pick Singleplayer or Multiplayer
3. Use the controls to move, jump, attack, and defend
4. First to win 2 rounds wins the match
5. After the game, you can restart or go back to the main menu

## 💡 Technical Details

- **Framework:** Pygame for the game
- **Resolution:** 1000x600 pixels
- **Frame Rate:** 60 FPS
- **AI:** Simple rule-based opponent that attacks at certain times
- **Collision:** Basic rectangle collision detection
- **Animation:** Frame-by-frame sprite animations

## 📚 What I Learned

This project helped me practice:
- Building a game loop
- Object-oriented programming in Python
- Handling sprite animations and assets
- Creating an AI opponent
- Designing user interfaces
- Managing user input and game states
- Keeping code organized

## 🤝 Contributing

This was a school project for my portfolio. Feel free to check it out and modify it for your own learning.

## 📄 License

This project is open source under the MIT License.

---

**Note:** I built this as part of my coursework at IEK AKMH. Some assets were created with AI tools, others I found online for free.</content>
