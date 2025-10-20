#!/usr/bin/env python3
"""
Zork AI Player - An AI agent that plays Zork using Claude
"""

import os
import sys
import subprocess
import time
import select
from anthropic import Anthropic

class ZorkPlayer:
    # ANSI color codes
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    GREY = '\033[90m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    def __init__(self, game_file, api_key=None, max_turns=50, verbose=False, save_file=None, auto_save=True):
        self.game_file = game_file
        self.max_turns = max_turns
        self.verbose = verbose
        self.save_file = save_file
        self.auto_save = auto_save
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        self.client = Anthropic(api_key=self.api_key)
        self.conversation_history = []
        self.game_process = None
        self.turn_count = 0
        
        # Set up save file path
        if not self.save_file:
            game_name = os.path.splitext(os.path.basename(game_file))[0]
            save_dir = os.path.join(os.path.dirname(game_file), 'saves')
            os.makedirs(save_dir, exist_ok=True)
            # Frotz uses .qzl extension for Quetzal save format
            self.save_file = os.path.join(save_dir, f'{game_name}_autosave.qzl')
        
    def _debug(self, message):
        """Print debug message if verbose mode is enabled"""
        if self.verbose:
            print(f"{self.GREY}{message}{self.RESET}", flush=True)
        
        # System prompt explaining Zork and how to play
        self.system_prompt = """You are an AI playing the classic text adventure game Zork I.

ABOUT ZORK:
Zork is a text adventure game set in the Great Underground Empire. Your goal is to explore this fantasy world, solve puzzles, collect treasures, and accumulate points. The game responds to natural language commands in the form of verb-noun combinations.

HOW TO PLAY:
- Use simple two-word commands like "GO NORTH", "TAKE LAMP", "OPEN DOOR"
- Common verbs: GO, TAKE, DROP, OPEN, CLOSE, READ, EXAMINE, ATTACK, INVENTORY
- Directions: NORTH, SOUTH, EAST, WEST, UP, DOWN, NORTHEAST, etc. (or N, S, E, W, U, D, NE, etc.)
- Type INVENTORY (or I) to see what you're carrying
- Type LOOK to see your current location description again
- Type EXAMINE [object] to look at something closely

GAME GOALS:
1. Explore the Great Underground Empire
2. Solve puzzles to access new areas
3. Find and collect treasures (usually worth points)
4. Avoid dangers and survive
5. Maximize your score

STRATEGY:
- Map areas mentally as you explore
- Examine everything carefully
- Try obvious actions first (take items, open containers)
- Keep a light source (the lamp is essential in dark areas)
- Save useful items - you can usually only carry a limited amount
- If stuck, try examining objects more carefully or revisiting areas

Play strategically and try to make meaningful progress. Output ONLY the next command you want to execute, nothing else. No explanations, just the command."""

    def start_game(self):
        """Start the Frotz process"""
        self._debug("Attempting to start Frotz...")
        try:
            self.game_process = subprocess.Popen(
                ['dfrotz', self.game_file],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0  # Unbuffered
            )
            self._debug("Frotz process started. Reading initial output...")
            # Wait longer for initial output
            time.sleep(1.5)
            return self._read_game_output(timeout=5)
        except FileNotFoundError:
            print("Error: dfrotz not found. Make sure Frotz is installed.")
            print("On Mac: brew install frotz")
            sys.exit(1)
        except Exception as e:
            print(f"Error starting game: {e}")
            sys.exit(1)
    
    def _read_game_output(self, timeout=3):
        """Read output from the game using non-blocking I/O"""
        output = []
        end_time = time.time() + timeout
        
        self._debug(f"Reading game output (timeout: {timeout}s)...")
        
        while time.time() < end_time:
            # Check if process is still alive
            if self.game_process.poll() is not None:
                self._debug("Game process ended")
                break
            
            # Use select to check if data is available (Unix-like systems)
            if sys.platform != 'win32':
                ready, _, _ = select.select([self.game_process.stdout], [], [], 0.1)
                if ready:
                    try:
                        char = self.game_process.stdout.read(1)
                        if char:
                            output.append(char)
                    except:
                        break
            else:
                # Windows fallback - use readline with shorter timeout
                try:
                    import threading
                    def read_line():
                        return self.game_process.stdout.readline()
                    
                    thread = threading.Thread(target=read_line)
                    thread.daemon = True
                    thread.start()
                    thread.join(0.1)
                    
                    if thread.is_alive():
                        time.sleep(0.1)
                        continue
                except:
                    break
        
        result = ''.join(output).strip()
        self._debug(f"Read {len(result)} characters from game")
        return result
    
    def send_command(self, command):
        """Send a command to the game"""
        if self.game_process and self.game_process.poll() is None:
            try:
                self._debug(f"Sending command to game: {command}")
                self.game_process.stdin.write(command + '\n')
                self.game_process.stdin.flush()
                time.sleep(0.5)  # Give game time to process
                return self._read_game_output()
            except Exception as e:
                self._debug(f"Error sending command: {e}")
                return "Error sending command"
        return "Game process not running"
    
    def get_ai_command(self, game_output):
        """Get next command from Claude"""
        self._debug("Requesting command from Claude...")
        
        # Add game output to conversation
        self.conversation_history.append({
            "role": "user",
            "content": f"Game output:\n{game_output}\n\nWhat's your next command?"
        })
        
        # Get response from Claude
        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=150,
            system=self.system_prompt,
            messages=self.conversation_history
        )
        
        command = response.content[0].text.strip()
        
        # Add AI's command to conversation
        self.conversation_history.append({
            "role": "assistant",
            "content": command
        })
        
        return command
    
    def save_game(self):
        """Save the current game state"""
        self._debug(f"Attempting to save game to: {self.save_file}")
        
        # Send SAVE command
        self.game_process.stdin.write('SAVE\n')
        self.game_process.stdin.flush()
        time.sleep(0.5)
        
        # Read prompt for filename
        prompt = self._read_game_output(timeout=2)
        self._debug(f"Save prompt: {prompt}")
        
        # Send filename
        self.game_process.stdin.write(self.save_file + '\n')
        self.game_process.stdin.flush()
        time.sleep(1)  # Give more time for save to complete
        
        # Read confirmation
        result = self._read_game_output(timeout=2)
        self._debug(f"Save result: {result}")
        
        # Check if save file exists (Frotz may add .qzl extension)
        save_exists = os.path.exists(self.save_file)
        save_with_qzl = os.path.exists(self.save_file + '.qzl')
        
        if save_exists or save_with_qzl:
            actual_file = self.save_file if save_exists else self.save_file + '.qzl'
            print(f"\n{self.GREEN}💾 Game saved to: {actual_file}{self.RESET}")
            
            # Send LOOK to refresh game state after save
            self.game_process.stdin.write('LOOK\n')
            self.game_process.stdin.flush()
            time.sleep(0.3)
            self._read_game_output(timeout=1)  # Clear the output
            
            return True
        else:
            print(f"\n{self.YELLOW}⚠️  Warning: Save file not created{self.RESET}")
            self._debug(f"Checked for: {self.save_file} and {self.save_file}.qzl")
            return False
    
    def restore_game(self):
        """Restore a saved game state"""
        # Check for save file with or without .qzl extension
        save_exists = os.path.exists(self.save_file)
        save_with_qzl = os.path.exists(self.save_file + '.qzl')
        
        if not save_exists and not save_with_qzl:
            print(f"\n{self.YELLOW}⚠️  No save file found at: {self.save_file}{self.RESET}")
            return False
        
        actual_file = self.save_file if save_exists else self.save_file + '.qzl'
        self._debug(f"Attempting to restore game from: {actual_file}")
        print(f"\n{self.CYAN}📂 Restoring from save file...{self.RESET}")
        
        # Send RESTORE command
        self.game_process.stdin.write('RESTORE\n')
        self.game_process.stdin.flush()
        time.sleep(0.5)
        
        # Read prompt for filename
        prompt = self._read_game_output(timeout=2)
        self._debug(f"Restore prompt: {prompt}")
        
        # Send filename (use actual file that exists)
        self.game_process.stdin.write(actual_file + '\n')
        self.game_process.stdin.flush()
        time.sleep(1)  # Give it more time to restore
        
        # Read confirmation
        result = self._read_game_output(timeout=3)
        self._debug(f"Initial restore result: {result}")
        
        # Send LOOK command to get current state description
        self.game_process.stdin.write('LOOK\n')
        self.game_process.stdin.flush()
        time.sleep(0.5)
        
        # Read the actual game state
        game_state = self._read_game_output(timeout=3)
        self._debug(f"Game state after LOOK: {game_state}")
        
        print(f"{self.GREEN}✓ Game restored from save file{self.RESET}")
        
        # Return the game state from LOOK command
        return game_state if game_state else result
    
    def play(self):
        """Main game loop"""
        print("Starting Zork AI Player...")
        print(f"Using game file: {self.game_file}")
        print(f"Max turns: {self.max_turns}")
        if self.auto_save:
            print(f"Auto-save: {self.save_file}")
        print()
        
        # Start the game
        initial_output = self.start_game()
        
        if not initial_output or len(initial_output) < 10:
            print("\nWARNING: Got very little output from game. There may be an issue.")
            print("Trying to continue anyway...\n")
        
        # Check if we should restore from save
        restore_from_save = False
        save_exists = os.path.exists(self.save_file) or os.path.exists(self.save_file + '.qzl')
        if save_exists:
            actual_file = self.save_file if os.path.exists(self.save_file) else self.save_file + '.qzl'
            print(f"\n{self.CYAN}Found existing save file: {actual_file}{self.RESET}")
            response = input(f"{self.CYAN}Resume from save? (y/n): {self.RESET}").strip().lower()
            restore_from_save = response in ['y', 'yes']
        
        if restore_from_save:
            game_output = self.restore_game()
            print("=" * 70)
            print(f"{self.MAGENTA}{self.BOLD}RESTORED GAME STATE:{self.RESET}")
            print("=" * 70)
            print(f"{self.YELLOW}{game_output}{self.RESET}")
            print("=" * 70)
        else:
            print("=" * 70)
            print(f"{self.MAGENTA}{self.BOLD}INITIAL GAME OUTPUT:{self.RESET}")
            print("=" * 70)
            print(f"{self.YELLOW}{initial_output}{self.RESET}")
            print("=" * 70)
            game_output = initial_output
        
        # Game loop
        for turn in range(1, self.max_turns + 1):
            self.turn_count = turn
            print(f"\n{'=' * 70}")
            print(f"{self.GREEN}{self.BOLD}▶ TURN {turn}{self.RESET}")
            print(f"{'=' * 70}")
            
            # Get command from AI
            command = self.get_ai_command(game_output)
            print(f"\n{self.CYAN}{self.BOLD}🤖 AI Command:{self.RESET} {self.CYAN}{command}{self.RESET}")
            
            # Check for quit
            if command.upper() in ['QUIT', 'Q']:
                print("\nAI decided to quit the game.")
                if self.auto_save:
                    self.save_game()
                break
            
            # Send command to game
            game_output = self.send_command(command)
            print(f"\n{self.YELLOW}{self.BOLD}📜 Game Response:{self.RESET}")
            print(f"{self.YELLOW}{game_output}{self.RESET}")
            
            # Check if game ended
            if "quit" in game_output.lower() or not game_output.strip():
                print("\nGame ended.")
                break
            
            # Auto-save every 10 turns
            if self.auto_save and turn % 10 == 0:
                self.save_game()
            
            # Small delay between turns
            time.sleep(0.5)
        
        # Final save before exit
        if self.auto_save and self.turn_count > 0:
            print(f"\n{self.CYAN}Saving final game state...{self.RESET}")
            self.save_game()
        
        # Clean up
        if self.game_process:
            self.game_process.terminate()
            self.game_process.wait()
        
        print(f"\n{'=' * 70}")
        print(f"{self.GREEN}{self.BOLD}✓ GAME SESSION COMPLETE{self.RESET}")
        print(f"Turns played: {self.turn_count}")
        if self.auto_save:
            save_exists = os.path.exists(self.save_file) or os.path.exists(self.save_file + '.qzl')
            if save_exists:
                actual_file = self.save_file if os.path.exists(self.save_file) else self.save_file + '.qzl'
                print(f"Save file: {actual_file}")
        print(f"{'=' * 70}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python zork_ai_player.py <path_to_zork.z5> [max_turns] [options]")
        print("\nOptions:")
        print("  --verbose, -v         Show debug messages in grey")
        print("  --no-autosave        Disable automatic saving")
        print("  --save-file <path>   Use custom save file path")
        print("\nExamples:")
        print("  python zork_ai_player.py games/zork1.z5 30")
        print("  python zork_ai_player.py games/zork1.z5 30 --verbose")
        print("  python zork_ai_player.py games/zork1.z5 50 --no-autosave")
        print("  python zork_ai_player.py games/zork1.z5 --save-file my_save.sav")
        sys.exit(1)
    
    game_file = sys.argv[1]
    max_turns = 50
    verbose = False
    auto_save = True
    save_file = None
    
    # Parse arguments
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--verbose' or arg == '-v':
            verbose = True
        elif arg == '--no-autosave':
            auto_save = False
        elif arg == '--save-file' and i + 1 < len(sys.argv):
            save_file = sys.argv[i + 1]
            i += 1
        elif arg.isdigit():
            max_turns = int(arg)
        i += 1
    
    if not os.path.exists(game_file):
        print(f"Error: Game file not found: {game_file}")
        sys.exit(1)
    
    # Test if dfrotz exists
    if verbose:
        try:
            result = subprocess.run(['which', 'dfrotz'], capture_output=True, text=True)
            print(f"Found dfrotz at: {result.stdout.strip()}")
        except:
            print("Warning: Could not verify dfrotz installation")
    
    player = ZorkPlayer(
        game_file, 
        max_turns=max_turns, 
        verbose=verbose,
        save_file=save_file,
        auto_save=auto_save
    )
    player.play()

if __name__ == "__main__":
    main()
