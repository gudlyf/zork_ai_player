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
    def __init__(self, game_file, api_key=None, max_turns=50):
        self.game_file = game_file
        self.max_turns = max_turns
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        self.client = Anthropic(api_key=self.api_key)
        self.conversation_history = []
        self.game_process = None
        
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
        print("Attempting to start Frotz...", flush=True)
        try:
            self.game_process = subprocess.Popen(
                ['dfrotz', self.game_file],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0  # Unbuffered
            )
            print("Frotz process started. Reading initial output...", flush=True)
            # Wait a moment for initial output
            time.sleep(1)
            return self._read_game_output()
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
        
        print(f"Reading game output (timeout: {timeout}s)...", flush=True)
        
        while time.time() < end_time:
            # Check if process is still alive
            if self.game_process.poll() is not None:
                print("Game process ended", flush=True)
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
        print(f"Read {len(result)} characters from game", flush=True)
        return result
    
    def send_command(self, command):
        """Send a command to the game"""
        if self.game_process and self.game_process.poll() is None:
            try:
                print(f"Sending command to game: {command}", flush=True)
                self.game_process.stdin.write(command + '\n')
                self.game_process.stdin.flush()
                time.sleep(0.5)  # Give game time to process
                return self._read_game_output()
            except Exception as e:
                print(f"Error sending command: {e}", flush=True)
                return "Error sending command"
        return "Game process not running"
    
    def get_ai_command(self, game_output):
        """Get next command from Claude"""
        print("Requesting command from Claude...", flush=True)
        
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
    
    def play(self):
        """Main game loop"""
        print("Starting Zork AI Player...")
        print(f"Using game file: {self.game_file}")
        print(f"Max turns: {self.max_turns}\n")
        
        # Start the game
        initial_output = self.start_game()
        
        if not initial_output or len(initial_output) < 10:
            print("\nWARNING: Got very little output from game. There may be an issue.")
            print("Trying to continue anyway...\n")
        
        print("=" * 70)
        print("INITIAL GAME OUTPUT:")
        print("=" * 70)
        print(initial_output)
        print("=" * 70)
        
        game_output = initial_output
        
        # Game loop
        for turn in range(1, self.max_turns + 1):
            print(f"\n{'=' * 70}")
            print(f"TURN {turn}")
            print(f"{'=' * 70}")
            
            # Get command from AI
            command = self.get_ai_command(game_output)
            print(f"AI Command: {command}")
            
            # Check for quit
            if command.upper() in ['QUIT', 'Q']:
                print("\nAI decided to quit the game.")
                break
            
            # Send command to game
            game_output = self.send_command(command)
            print(f"\nGame Response:\n{game_output}")
            
            # Check if game ended
            if "quit" in game_output.lower() or not game_output.strip():
                print("\nGame ended.")
                break
            
            # Small delay between turns
            time.sleep(0.5)
        
        # Clean up
        if self.game_process:
            self.game_process.terminate()
            self.game_process.wait()
        
        print(f"\n{'=' * 70}")
        print("GAME SESSION COMPLETE")
        print(f"{'=' * 70}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python zork_ai_player.py <path_to_zork.z5> [max_turns]")
        print("\nExample:")
        print("  python zork_ai_player.py games/zork1.z5 30")
        sys.exit(1)
    
    game_file = sys.argv[1]
    max_turns = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    if not os.path.exists(game_file):
        print(f"Error: Game file not found: {game_file}")
        sys.exit(1)
    
    # Test if dfrotz exists
    try:
        result = subprocess.run(['which', 'dfrotz'], capture_output=True, text=True)
        print(f"Found dfrotz at: {result.stdout.strip()}")
    except:
        print("Warning: Could not verify dfrotz installation")
    
    player = ZorkPlayer(game_file, max_turns=max_turns)
    player.play()

if __name__ == "__main__":
    main()
