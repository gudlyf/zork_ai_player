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

This will install:
- `anthropic` - Claude API client
- `pexpect` - For reliable interaction with Frotz

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

With verbose debug output:
```bash
python zork_ai_player.py games/zork1.z5 50 --verbose
# or
python zork_ai_player.py games/zork1.z5 50 -v
```

Disable auto-save:
```bash
python zork_ai_player.py games/zork1.z5 50 --no-autosave
```

Use custom save file:
```bash
python zork_ai_player.py games/zork1.z5 --save-file my_custom_save.sav
```

**Options:**
- First argument: Path to game file (required)
- Second argument: Number of turns (default: 50)
- `--verbose` or `-v`: Show debug messages in grey (optional)
- `--no-autosave`: Disable automatic saving (optional)
- `--save-file <path>`: Specify custom save file location (optional)

The AI will:
1. Read the game's text output
2. Analyze the situation using previous knowledge
3. Decide on the best command
4. Execute the command
5. Learn from the interaction
6. Repeat until the game ends or max turns reached

**Learning System in Action:**
```
📚 Loaded previous learning: 15 facts, 8 locations, 12 items
▶ TURN 1
🤖 AI Command: EXAMINE LAMP
📜 Game Response: The lamp is on and provides light...
```

The AI remembers what it learned in previous sessions and uses this knowledge to make better decisions.

## How It Works

1. **Frotz Interface**: Uses `dfrotz` (dumb frotz) to run the Z-machine game file via subprocess
2. **Claude Integration**: Sends game text to Claude along with instructions about Zork
3. **Command Loop**: AI generates commands, sends them to Frotz, and reads responses
4. **Learning System**: AI learns from its experiences and builds knowledge across sessions
5. **System Prompt**: Includes detailed instructions about:
   - How Zork works
   - Valid command syntax
   - Game objectives
   - Strategy tips
   - Special game mechanics (like "passes through" objects)

**Output Formatting:**
- 🤖 **AI Commands** - Displayed in **cyan** 
- 📜 **Game Responses** - Displayed in **yellow**
- ▶ **Turn Headers** - Displayed in **green**
- Debug messages (with `--verbose`) - Displayed in **grey**

## Save & Resume Feature

The application automatically saves your game progress:

**Auto-Save Behavior:**
- Saves every 10 turns automatically
- Saves when you exit or quit
- Saves to `games/saves/<gamename>_autosave.qzl` by default (Quetzal format)

**Resuming from Save:**
When you restart the application, if a save file exists, you'll be prompted:
```
Found existing save file: games/saves/zork1_autosave.qzl
Resume from save? (y/n):
```

Type `y` to continue from where you left off, or `n` to start fresh.

**Custom Save File:**
```bash
# Use your own save file location (Frotz will add .qzl if needed)
python zork_ai_player.py games/zork1.z5 --save-file my_progress.qzl
```

**Disable Auto-Save:**
```bash
# Run without saving (useful for testing)
python zork_ai_player.py games/zork1.z5 --no-autosave
```

**How It Works:**
The application uses Zork's built-in SAVE and RESTORE commands. Save files are created in Quetzal format (.qzl) by Frotz and are compatible with any Z-machine interpreter (you could load them in a regular Frotz session).

## AI Learning System 🧠

The AI player includes an intelligent learning system that captures knowledge across game sessions:

**What the AI Learns:**
- **Location Insights**: Details about rooms, passages, traps, and treasures
- **Item Information**: What items do, where they're found, how to use them
- **Puzzle Solutions**: Hints about locked doors, switches, and other obstacles
- **General Facts**: What works, what doesn't, and successful strategies

**Learning Features:**
- **Persistent Memory**: AI remembers discoveries from previous sessions
- **Smart Context**: Only relevant knowledge is provided to keep token usage low
- **Automatic Extraction**: Learning happens automatically during gameplay
- **Efficient Storage**: Knowledge saved as lightweight JSON files

**Learning Files:**
- `games/saves/zork1_learning.json` - Contains AI's accumulated knowledge
- Automatically saved every 10 turns and when exiting
- Loaded automatically when resuming a game

**Example Learning Data:**
```json
{
  "learned_facts": [
    "Cannot open door - It's locked",
    "Successfully took lamp with TAKE LAMP"
  ],
  "location_insights": {
    "Living Room": ["There is a lamp here", "Passage to north"]
  },
  "item_insights": {
    "lamp": "A brass lamp that provides light"
  },
  "puzzle_solutions": {
    "door_puzzle": "Need to find key"
  }
}
```

**Benefits:**
- AI makes better decisions based on previous experience
- Avoids repeating failed strategies
- Remembers successful approaches
- Builds knowledge progressively across sessions

## Project Structure

```
~/gudlyf/src/zork_ai/
├── zork_ai_player.py    # Main application
├── requirements.txt     # Python dependencies
├── README.md            # This file
└── games/
    ├── zork1.z5         # Zork game file (you provide this)
    └── saves/           # Auto-generated save files
        ├── zork1_autosave.qzl      # Quetzal save format
        └── zork1_learning.json     # AI learning data
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
- Run with `--verbose` flag to see debug messages
- Check if `dfrotz` is working: `dfrotz games/zork1.z5`

## About Zork

Zork I: The Great Underground Empire is one of the earliest text adventure games, originally developed at MIT in the late 1970s and commercially released by Infocom in 1980. It's a pioneering work in interactive fiction that has influenced countless games since.

The game is freely distributed by Activision (who acquired Infocom) and is considered a classic of computing history.

## License

This code is provided as-is for educational purposes. 

Zork is copyright Activision/Infocom. The game files are distributed freely by Activision.

## Notes

- The AI may not always make optimal decisions
- Some puzzles in Zork are quite difficult even for AI
- You can interrupt the program with Ctrl+C (will auto-save if enabled)
- The learning system keeps token usage low by only storing key insights
- Use `--verbose` flag to see detailed debug information
- Colors are supported on most modern terminals (macOS Terminal, iTerm2, Linux terminals)
- Save files are stored in `games/saves/` in Quetzal format (.qzl) and are compatible with any Frotz interpreter
- Learning data is stored in JSON format and persists across sessions
- When resuming, the AI continues from the saved game state with full context and previous knowledge
- The AI learns from "passes through" mechanics and other special game features
