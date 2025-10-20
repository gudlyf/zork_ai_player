# Quick Start Guide

Get up and running with Zork AI Player in 5 minutes.

## Prerequisites

- macOS (instructions included for Linux)
- Terminal access
- Anthropic API key ([get one here](https://console.anthropic.com/))

## Setup (5 minutes)

### 1. Install Frotz

```bash
brew install frotz
```

### 2. Create Project

```bash
mkdir -p ~/gudlyf/src/zork_ai/games
cd ~/gudlyf/src/zork_ai
```

### 3. Create Files

Save the following files to `~/gudlyf/src/zork_ai/`:
- `zork_ai_player.py` - Main application
- `requirements.txt` - Dependencies
- `README.md` - Full documentation

### 4. Install Dependencies

```bash
pip3 install anthropic
```

### 5. Set API Key

```bash
export ANTHROPIC_API_KEY='sk-ant-xxxxx'
```

### 6. Download Zork

**Quick Download Links:**

You can get Zork I from the Internet Archive or IFDB. Here are direct approaches:

**Method 1: Using curl (easiest)**
```bash
cd ~/gudlyf/src/zork_ai/games

# Download from a mirror (check if available)
# Note: You may need to find a current direct link
```

**Method 2: Manual Download**
1. Visit: https://www.ifarchive.org/indexes/if-archiveXgamesXzcode.html
2. Search for "Zork" 
3. Download `zork1.z5` or extract from zip
4. Move to: `~/gudlyf/src/zork_ai/games/zork1.z5`

**Method 3: From Classic Archive**
```bash
# If you find a direct link, use wget or curl
cd ~/gudlyf/src/zork_ai/games
curl -O [URL-to-zork1.z5]
```

**Verify the file:**
```bash
file games/zork1.z5
# Should output: "Z-machine type 3 byte code"
```

## Run

```bash
cd ~/gudlyf/src/zork_ai
python3 zork_ai_player.py games/zork1.z5
```

Watch as Claude plays Zork!

## Example Output

```
Starting Zork AI Player...
Using game file: games/zork1.z5
Max turns: 50

==================================================
INITIAL GAME OUTPUT:
==================================================
ZORK I: The Great Underground Empire
Copyright (c) 1981, 1982, 1983 Infocom, Inc.
All rights reserved.
ZORK is a registered trademark of Infocom, Inc.

West of House
You are standing in an open field west of a white house...
==================================================

==================================================
TURN 1
==================================================
AI Command: EXAMINE HOUSE

Game Response:
The house is a beautiful colonial style house...
```

## Common Issues

**"dfrotz not found"**
```bash
brew install frotz
```

**"ANTHROPIC_API_KEY not set"**
```bash
export ANTHROPIC_API_KEY='your-key-here'
```

**"Game file not found"**
```bash
# Check file location
ls -la ~/gudlyf/src/zork_ai/games/
```

## Configuration

### Change Number of Turns

```bash
python3 zork_ai_player.py games/zork1.z5 100  # 100 turns instead of 50
```

### Use Different Model

Edit `zork_ai_player.py`, line with model name:
```python
model="claude-sonnet-4-5-20250929",  # Change to another model
```

## Tips

- **Watch the score**: The AI tries to maximize points
- **Interrupt anytime**: Press `Ctrl+C` to stop
- **Cost awareness**: Each turn costs API tokens
- **Better results**: Give the AI more turns for better exploration
- **Debug mode**: Add print statements to see AI's reasoning

## Next Steps

- Read `README.md` for full documentation
- Modify the system prompt in `zork_ai_player.py` to change AI behavior
- Try other Infocom games (Zork II, III, Hitchhiker's Guide, etc.)
- Adapt the code for OpenAI's GPT models

## Alternative: Docker Setup

If you prefer Docker:

```bash
# Pull Frotz container
docker pull newtmitch/frotz

# Run with volume mount
docker run -it -v ~/gudlyf/src/zork_ai/games:/games newtmitch/frotz /games/zork1.z5
```

Then adapt the Python code to use Docker exec instead of subprocess.

---

**Enjoy watching Claude explore the Great Underground Empire!**
