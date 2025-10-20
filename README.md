# Zork AI Player

An AI-powered player for the classic text adventure game Zork using Claude.

## Overview

This application interfaces with Zork I (a classic text adventure game) and uses Claude AI to read game descriptions, make decisions, and enter commands to progress through the game.

## Prerequisites

- **Python 3.8+**
- **Frotz** (Z-machine interpreter)
- **Anthropic API Key**
- **Zork I game file** (.z5 format)

## Installation

### 1. Install Frotz

On macOS:
```bash
brew install frotz
```

On Linux:
```bash
# Ubuntu/Debian
sudo apt-get install frotz

# Fedora
sudo dnf install frotz

# Arch
sudo pacman -S frotz
```

### 2. Clone or Create Project Directory

```bash
mkdir -p ~/gudlyf/src/zork_ai
cd ~/gudlyf/src/zork_ai
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up API Key

Export your Anthropic API key:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

Or add it to your `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### 5. Download Zork I

Zork I, II, and III are freely distributed by Activision. You can download them from several sources:

**Option 1: IFDB (Interactive Fiction Database)**
- Visit: https://ifdb.org/viewgame?id=4gxk83ja4twckm6j
- Click "Play Online" or download the `.z5` file

**Option 2: IF Archive**
- Visit: http://www.ifarchive.org/indexes/if-archiveXgamesXzcode.html
- Look for Zork game files

**Option 3: Direct Download**
Several sites host the legal, free versions:
- The file is typically named `ZORK1.DAT` or `zork1.z5`
- You may need to extract it from a `.zip` file
- If the file has a `.DAT` extension, rename it to `.z5`

Save the file to your project:
```bash
mkdir -p ~/gudlyf/src/zork_ai/games
# Move your downloaded file
mv ~/Downloads/zork1.z5 ~/gudlyf/src/zork_ai/games/
```

## Usage

Run the AI player:

```bash
cd ~/gudlyf/src/zork_ai
python zork_ai_player.py games/zork1.z5
```

With custom number of turns:
```bash
python zork_ai_player.py games/zork1.z5 30
```

The AI will:
1. Read the game's text output
2. Analyze the situation
3. Decide on the best command
4. Execute the command
5. Repeat until the game ends or max turns reached

## How It Works

1. **Frotz Interface**: Uses `dfrotz` (dumb frotz) to run the Z-machine game file via subprocess
2. **Claude Integration**: Sends game text to Claude along with instructions about Zork
3. **Command Loop**: AI generates commands, sends them to Frotz, and reads responses
4. **System Prompt**: Includes detailed instructions about:
   - How Zork works
   - Valid command syntax
   - Game objectives
   - Strategy tips

## Project Structure

```
~/gudlyf/src/zork_ai/
├── zork_ai_player.py    # Main application
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── games/
    └── zork1.z5         # Zork game file (you provide this)
```

## Customization

### Using OpenAI Instead of Claude

To use OpenAI's API instead, modify the `zork_ai_player.py` to use the OpenAI SDK:

```python
from openai import OpenAI

client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": self.system_prompt},
        *self.conversation_history
    ]
)
command = response.choices[0].message.content
```

### Adjusting AI Behavior

Edit the `system_prompt` in `zork_ai_player.py` to change:
- Play style (aggressive vs cautious)
- Focus (exploration vs treasure hunting)
- Command complexity
- Strategy approach

## Troubleshooting

**dfrotz not found:**
```bash
# Make sure Frotz is installed
brew install frotz  # macOS
which dfrotz        # Should show path to binary
```

**API Key Error:**
```bash
# Verify your key is set
echo $ANTHROPIC_API_KEY
```

**Game file not loading:**
```bash
# Check file exists and is readable
ls -la games/zork1.z5
file games/zork1.z5  # Should show "Z-machine"
```

**No game output:**
- Increase timeouts in `_read_game_output()` method
- Add debug print statements to see what's happening

## About Zork

Zork I: The Great Underground Empire is one of the earliest text adventure games, originally developed at MIT in the late 1970s and commercially released by Infocom in 1980. It's a pioneering work in interactive fiction that has influenced countless games since.

The game is freely distributed by Activision (who acquired Infocom) and is considered a classic of computing history.

## License

This code is provided as-is for educational purposes. 

Zork is copyright Activision/Infocom. The game files are distributed freely by Activision.

## Notes

- The AI may not always make optimal decisions
- Some puzzles in Zork are quite difficult even for AI
- You can interrupt the program with Ctrl+C
- The conversation history grows with each turn, affecting API costs
