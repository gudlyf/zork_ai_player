# Quick Start Guide

Get up and running with Zork AI Player in 5 minutes.

## Prerequisites

- macOS (instructions included for Linux)
- Terminal access
- AI Provider (choose one):
  - Anthropic API key ([get one here](https://console.anthropic.com/))
  - Ollama (for local models)

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
pip3 install anthropic pexpect
```

### 5. Set Up AI Provider

**Option A: Anthropic API**
```bash
export ANTHROPIC_API_KEY='sk-ant-xxxxx'
```

**Option B: Ollama (Local)**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.2

# Start server
ollama serve
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

**For debug mode:**
```bash
python3 zork_ai_player.py games/zork1.z5 50 --verbose
```

Watch as Claude plays Zork!

## Example Output

```
Starting Zork AI Player...
Using game file: games/zork1.z5
Max turns: 50

======================================================================
INITIAL GAME OUTPUT:
======================================================================
ZORK I: The Great Underground Empire
Copyright (c) 1981, 1982, 1983 Infocom, Inc.
All rights reserved.
ZORK is a registered trademark of Infocom, Inc.

West of House
You are standing in an open field west of a white house...
======================================================================

======================================================================
▶ TURN 1
======================================================================

🤖 AI Command: EXAMINE HOUSE

📜 Game Response:
The house is a beautiful colonial house...

======================================================================
▶ TURN 2
======================================================================

🤖 AI Command: GO NORTH

📜 Game Response:
North of House
You are facing the north side of a white house...
```

**Note:** AI Commands appear in cyan, Game Responses in yellow. 
Add `--verbose` to see grey debug messages about timeouts and I/O.

## AI Learning System 🧠

The AI player includes an intelligent learning system that captures knowledge across game sessions:

**What the AI Learns:**
- **Location Insights**: Details about rooms, passages, traps, and treasures
- **Item Information**: What items do, where they're found, how to use them
- **Puzzle Solutions**: Hints about locked doors, switches, and other obstacles
- **General Facts**: What works, what doesn't, and successful strategies
- **Map Data**: Location connections, navigation paths, and spatial relationships

**Learning Features:**
- **Persistent Memory**: AI remembers discoveries from previous sessions
- **Smart Context**: Only relevant knowledge is provided to keep token usage low
- **Automatic Extraction**: Learning happens automatically during gameplay
- **Efficient Storage**: Knowledge saved as lightweight JSON files
- **Map Building**: Creates a mental map of locations and connections
- **Navigation Memory**: Remembers where it can go from each location

**Learning Files:**
- `games/saves/zork1_learning.json` - Contains AI's accumulated knowledge
- Automatically saved every 10 turns and when exiting
- Loaded automatically when resuming a game

**Benefits:**
- AI makes better decisions based on previous experience
- Avoids repeating failed strategies
- Remembers successful approaches
- Builds knowledge progressively across sessions
- Creates a mental map for better navigation
- Remembers location connections and exits

## Save & Resume

The game auto-saves every 10 turns in Quetzal format (.qzl). When you run it again:

```
Found existing save file: games/saves/zork1_autosave.qzl
Resume from save? (y/n): y
```

Type `y` to continue, `n` to start over.

**Learning System Integration:**
- AI learning data is automatically saved alongside game saves
- When resuming, the AI loads both game state and previous knowledge
- The AI makes better decisions based on what it learned before

**Run without saving:**
```bash
python3 zork_ai_player.py games/zork1.z5 --no-autosave
```

**Use Ollama instead:**
```bash
python3 zork_ai_player.py games/zork1.z5 --ollama
```

**Use specific Ollama model:**
```bash
python3 zork_ai_player.py games/zork1.z5 --ollama --ollama-model llama3.2
```

**Debug the learning system:**
```bash
python3 zork_ai_player.py games/zork1.z5 --verbose
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

**Program seems frozen**
```bash
# Run with verbose mode to see what's happening
python3 zork_ai_player.py games/zork1.z5 50 --verbose
```

## Configuration

### Change Number of Turns

```bash
python3 zork_ai_player.py games/zork1.z5 100  # 100 turns instead of 50
```

### Enable Debug Output

```bash
python3 zork_ai_player.py games/zork1.z5 50 --verbose  # Shows grey debug messages
```

### Long Sessions with Auto-Save

```bash
# Run for 100 turns - auto-saves every 10 turns
python3 zork_ai_player.py games/zork1.z5 100

# Resume the next day from where you left off
python3 zork_ai_player.py games/zork1.z5 100
# (When prompted, type 'y' to resume)
```

### Use Different Model

Edit `zork_ai_player.py`, line with model name:
```python
model="claude-sonnet-4-5-20250929",  # Change to another model
```

## Tips

- **Watch the score**: The AI tries to maximize points
- **Interrupt anytime**: Press `Ctrl+C` to stop (auto-saves before exit)
- **Cost awareness**: Each turn costs API tokens
- **Better results**: Give the AI more turns for better exploration
- **Debug mode**: Use `--verbose` to see grey debug messages about I/O and timeouts
- **Clean output**: Run without `--verbose` for just AI commands and game responses
- **Resume later**: The game auto-saves, so you can stop and continue anytime
- **Long sessions**: Run for 100+ turns and let it save progress every 10 turns

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
