#!/usr/bin/env python3
"""
Zork AI Player - An AI agent that plays Zork using Claude
"""

import os
import sys
import time
import pexpect
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
        
        # Learning system - lightweight knowledge capture
        self.learned_facts = []
        self.location_insights = {}  # location -> insights
        self.item_insights = {}      # item -> insights
        self.puzzle_solutions = {}   # puzzle -> solution
        self.learning_file = None
        
        # Set up save file path
        if not self.save_file:
            game_name = os.path.splitext(os.path.basename(game_file))[0]
            save_dir = os.path.join(os.path.dirname(game_file), 'saves')
            os.makedirs(save_dir, exist_ok=True)
            # Frotz uses .qzl extension for Quetzal save format
            self.save_file = os.path.join(save_dir, f'{game_name}_autosave.qzl')
        
        # Set up learning file path
        self.learning_file = os.path.join(save_dir, f'{game_name}_learning.json')
        
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
- NEVER quit the game - always try different approaches when stuck, unless you are dead in a ghost world
- If you can't progress in one direction, try exploring other areas
- Use INVENTORY to see what you have and think of creative uses for items

SPECIAL MECHANICS:
- If the game says your hand "passes through" an object, it means your character is dead and you are in a ghost world
- You can't interact with solid objects when dead - you must restart the game
- Try RESTART command to start over, or QUIT and restart the program if RESTART doesn't work
- This usually happens when you die in the game - you become a ghost and can't interact with the physical world

Play strategically and try to make meaningful progress. Output ONLY the next command you want to execute, nothing else. No explanations, just the command."""

    def start_game(self):
        """Start the Frotz process using pexpect"""
        self._debug("Attempting to start Frotz with pexpect...")
        try:
            # Spawn frotz with pexpect - it handles pseudo-terminals automatically
            self.game_process = pexpect.spawn(
                f'dfrotz {self.game_file}',
                encoding='utf-8',
                timeout=30
            )
            
            self._debug("Waiting for initial game prompt...")
            # Wait for the initial '>' prompt
            self.game_process.expect('>', timeout=10)
            
            # Get all the text that appeared before the prompt
            initial_output = self.game_process.before
            
            self._debug(f"Captured {len(initial_output)} characters of initial output")
            return initial_output
            
        except FileNotFoundError:
            print("Error: dfrotz not found. Make sure Frotz is installed.")
            print("On Mac: brew install frotz")
            sys.exit(1)
        except pexpect.TIMEOUT:
            print("Error: Timeout waiting for game to start")
            sys.exit(1)
        except Exception as e:
            print(f"Error starting game: {e}")
            sys.exit(1)
    
    def _read_game_output(self, timeout=5, wait_for_prompt=True):
        """Read output from the game until we see the prompt"""
        output = []
        end_time = time.time() + timeout
        last_char_time = time.time()
        
        self._debug(f"Reading game output (timeout: {timeout}s, wait_for_prompt: {wait_for_prompt})...")
        
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
                            last_char_time = time.time()
                    except:
                        break
                else:
                    # No data available right now
                    if output and wait_for_prompt:
                        # Check if we have a prompt at the end
                        output_str = ''.join(output)
                        # Look for prompt pattern: newline followed by > and then nothing/whitespace
                        if output_str.rstrip().endswith('\n>') or output_str.endswith('> '):
                            self._debug("Found prompt pattern, stopping read")
                            break
                    
                    # If no new data for 2 seconds, stop
                    if output and (time.time() - last_char_time) > 2.0:
                        self._debug("No new data for 2s, stopping")
                        break
            else:
                # Windows fallback
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
        self._debug(f"Read {len(result)} characters")
        return result
    
    def send_command(self, command):
        """Send a command to the game and get response"""
        if self.game_process and self.game_process.isalive():
            try:
                self._debug(f"Sending command: {command}")
                
                # Send the command
                self.game_process.sendline(command)
                
                # Wait for the next prompt
                self.game_process.expect('>', timeout=10)
                
                # Get everything that appeared before the prompt
                response = self.game_process.before
                
                self._debug(f"Got response: {len(response)} characters")
                return response.strip()
                
            except pexpect.TIMEOUT:
                self._debug("Timeout waiting for response")
                return "Error: Game did not respond in time"
            except Exception as e:
                self._debug(f"Error sending command: {e}")
                return f"Error sending command: {e}"
        return "Game process not running"
    
    def get_ai_command(self, game_output):
        """Get next command from Claude"""
        self._debug("Requesting command from Claude...")
        
        # Get learning context
        learning_context = self.get_learning_context()
        
        # Create enhanced prompt with learning
        enhanced_prompt = self.system_prompt
        if learning_context:
            enhanced_prompt += f"\n\nPREVIOUS KNOWLEDGE:\n{learning_context}\n\nUse this knowledge to make better decisions."
        
        # Add game output to conversation
        self.conversation_history.append({
            "role": "user",
            "content": f"Game output:\n{game_output}\n\nWhat's your next command?"
        })
        
        # Get response from Claude
        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=150,
            system=enhanced_prompt,
            messages=self.conversation_history
        )
        
        command = response.content[0].text.strip()
        
        # Add AI's command to conversation
        self.conversation_history.append({
            "role": "assistant",
            "content": command
        })
        
        return command
    
    def extract_learning(self, game_output, command, response):
        """Extract key learning from game interaction"""
        # Look for important patterns in the game output
        important_patterns = [
            "You can't", "You need", "It's locked", "The door is", "You see",
            "There is", "You find", "You take", "You drop", "You open",
            "You close", "You read", "You examine", "You attack", "You die"
        ]
        
        # Extract location information
        if "You are in" in game_output or "You are at" in game_output:
            location = self._extract_location(game_output)
            if location:
                self.location_insights[location] = self._summarize_location(game_output)
        
        # Extract item information
        if any(pattern in game_output for pattern in ["You take", "You find", "You see"]):
            items = self._extract_items(game_output)
            for item in items:
                self.item_insights[item] = self._summarize_item(game_output, item)
        
        # Extract puzzle solutions
        if "You can't" in response and "You need" in game_output:
            puzzle = self._identify_puzzle(game_output)
            if puzzle:
                self.puzzle_solutions[puzzle] = self._extract_solution_hint(game_output)
        
        # Extract general facts
        if any(pattern in game_output for pattern in important_patterns):
            fact = self._extract_fact(game_output, command, response)
            if fact:
                self.learned_facts.append(fact)
    
    def _extract_location(self, game_output):
        """Extract current location from game output"""
        lines = game_output.split('\n')
        for line in lines:
            if "You are in" in line or "You are at" in line:
                # Extract location name (usually the first line after "You are in/at")
                return line.strip()
        return None
    
    def _summarize_location(self, game_output):
        """Create a brief summary of location insights"""
        # Extract key details about the location
        key_details = []
        lines = game_output.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['door', 'passage', 'stair', 'ladder', 'trap', 'treasure', 'monster']):
                key_details.append(line)
        
        return key_details[:3]  # Keep only top 3 insights
    
    def _extract_items(self, game_output):
        """Extract items mentioned in the game output"""
        items = []
        lines = game_output.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['you take', 'you find', 'you see']):
                # Extract item names (simple heuristic)
                words = line.split()
                for i, word in enumerate(words):
                    if word.lower() in ['take', 'find', 'see'] and i + 1 < len(words):
                        items.append(words[i + 1])
        
        return items
    
    def _summarize_item(self, game_output, item):
        """Create a brief summary of item insights"""
        # Look for descriptions of the item
        lines = game_output.split('\n')
        for line in lines:
            if item.lower() in line.lower() and len(line) > 10:
                return line.strip()
        return f"Found {item}"
    
    def _identify_puzzle(self, game_output):
        """Identify if there's a puzzle to solve"""
        if "You can't" in game_output and any(keyword in game_output.lower() for keyword in ['door', 'gate', 'passage', 'open']):
            return "door_puzzle"
        return None
    
    def _extract_solution_hint(self, game_output):
        """Extract hints about puzzle solutions"""
        lines = game_output.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['key', 'lever', 'button', 'switch', 'password']):
                return line.strip()
        return "Need to find solution"
    
    def _extract_fact(self, game_output, command, response):
        """Extract a general fact from the interaction"""
        # Create a concise fact about what happened
        if "You can't" in response:
            return f"Cannot {command.lower()} - {response[:50]}"
        elif "You take" in response:
            return f"Successfully took item with {command}"
        elif "You open" in response:
            return f"Successfully opened with {command}"
        return None
    
    def save_learning(self):
        """Save learning data to file"""
        import json
        
        learning_data = {
            'learned_facts': self.learned_facts[-20:],  # Keep only last 20 facts
            'location_insights': self.location_insights,
            'item_insights': self.item_insights,
            'puzzle_solutions': self.puzzle_solutions,
            'turn_count': self.turn_count
        }
        
        try:
            with open(self.learning_file, 'w') as f:
                json.dump(learning_data, f, indent=2)
            self._debug(f"Learning saved to: {self.learning_file}")
        except Exception as e:
            self._debug(f"Error saving learning: {e}")
    
    def load_learning(self):
        """Load learning data from file"""
        import json
        
        if not os.path.exists(self.learning_file):
            return False
        
        try:
            with open(self.learning_file, 'r') as f:
                learning_data = json.load(f)
            
            self.learned_facts = learning_data.get('learned_facts', [])
            self.location_insights = learning_data.get('location_insights', {})
            self.item_insights = learning_data.get('item_insights', {})
            self.puzzle_solutions = learning_data.get('puzzle_solutions', {})
            
            self._debug(f"Learning loaded from: {self.learning_file}")
            return True
        except Exception as e:
            self._debug(f"Error loading learning: {e}")
            return False
    
    def get_learning_context(self):
        """Get relevant learning context for AI without full conversation history"""
        context = []
        
        # Add recent facts (last 5)
        if self.learned_facts:
            context.append("Recent discoveries:")
            for fact in self.learned_facts[-5:]:
                context.append(f"- {fact}")
        
        # Add location insights if we have them
        if self.location_insights:
            context.append("\nKnown locations:")
            for location, insights in list(self.location_insights.items())[-3:]:
                context.append(f"- {location}: {', '.join(insights[:2])}")
        
        # Add item insights
        if self.item_insights:
            context.append("\nKnown items:")
            for item, insight in list(self.item_insights.items())[-3:]:
                context.append(f"- {item}: {insight}")
        
        # Add puzzle solutions
        if self.puzzle_solutions:
            context.append("\nPuzzle solutions:")
            for puzzle, solution in self.puzzle_solutions.items():
                context.append(f"- {puzzle}: {solution}")
        
        return "\n".join(context) if context else ""
    
    def save_game(self):
        """Save the current game state"""
        self._debug(f"Attempting to save game to: {self.save_file}")
        
        try:
            # Send SAVE command
            self.game_process.sendline('SAVE')
            
            # Wait for filename prompt - look for bracket or colon
            idx = self.game_process.expect(['\\[', ':', pexpect.TIMEOUT], timeout=5)
            prompt = self.game_process.before
            self._debug(f"Save prompt (matched pattern {idx}): {prompt}")
            
            # Read until the prompt character if we haven't consumed it
            if idx in [0, 1]:  # Found [ or :
                # Read to end of line to get full prompt
                try:
                    self.game_process.expect('\n', timeout=1)
                except:
                    pass
            
            # Send filename
            self.game_process.sendline(self.save_file)
            
            # Check for "Overwrite existing file?" prompt
            try:
                # Wait a moment for potential overwrite prompt
                overwrite_idx = self.game_process.expect(['Overwrite existing file', '>', pexpect.TIMEOUT], timeout=3)
                if overwrite_idx == 0:  # Found overwrite prompt
                    self._debug("Found overwrite prompt, responding with 'yes'")
                    self.game_process.sendline('yes')
                    # Wait for the result after overwrite confirmation
                    self.game_process.expect('>', timeout=10)
                elif overwrite_idx == 1:  # Found prompt directly (no overwrite needed)
                    pass  # Already at prompt
                else:  # Timeout - assume no overwrite needed
                    pass
            except pexpect.TIMEOUT:
                # No overwrite prompt, continue
                pass
            
            # Get the final result
            result = self.game_process.before
            self._debug(f"Save result: {result}")
            
            # Check if save file exists
            save_exists = os.path.exists(self.save_file)
            save_with_qzl = os.path.exists(self.save_file + '.qzl')
            
            if save_exists or save_with_qzl:
                actual_file = self.save_file if save_exists else self.save_file + '.qzl'
                print(f"\n{self.GREEN}💾 Game saved to: {actual_file}{self.RESET}")
                save_success = True
            else:
                print(f"\n{self.YELLOW}⚠️  Warning: Save file not created{self.RESET}")
                save_success = False
            
            # Send LOOK to refresh game state
            self.game_process.sendline('LOOK')
            self.game_process.expect('>', timeout=5)
            current_state = self.game_process.before.strip()
            
            return save_success, current_state
            
        except pexpect.TIMEOUT as e:
            print(f"\n{self.YELLOW}⚠️  Timeout during save{self.RESET}")
            self._debug(f"Timeout detail: {e}")
            # Try to recover by reading what we have
            try:
                remaining = self.game_process.read_nonblocking(size=1000, timeout=0.5)
                self._debug(f"Remaining output: {remaining}")
            except:
                pass
            return False, ""
        except Exception as e:
            self._debug(f"Save error: {e}")
            return False, ""
    
    def restore_game(self):
        """Restore a saved game state"""
        # Check for save file
        save_exists = os.path.exists(self.save_file)
        save_with_qzl = os.path.exists(self.save_file + '.qzl')
        
        if not save_exists and not save_with_qzl:
            print(f"\n{self.YELLOW}⚠️  No save file found{self.RESET}")
            return False
        
        actual_file = self.save_file if save_exists else self.save_file + '.qzl'
        self._debug(f"Restoring from: {actual_file}")
        print(f"\n{self.CYAN}📂 Restoring from save file...{self.RESET}")
        
        try:
            # Send RESTORE command
            self.game_process.sendline('RESTORE')
            
            # Wait for filename prompt - look for bracket or colon
            idx = self.game_process.expect(['\\[', ':', pexpect.TIMEOUT], timeout=5)
            self._debug(f"Restore prompt (matched pattern {idx})")
            
            # Read until end of prompt line
            if idx in [0, 1]:
                try:
                    self.game_process.expect('\n', timeout=1)
                except:
                    pass
            
            # Send filename
            self.game_process.sendline(actual_file)
            
            # Check for "Overwrite existing file?" prompt
            try:
                # Wait a moment for potential overwrite prompt
                overwrite_idx = self.game_process.expect(['Overwrite existing file', '>', pexpect.TIMEOUT], timeout=3)
                if overwrite_idx == 0:  # Found overwrite prompt
                    self._debug("Found overwrite prompt during restore, responding with 'yes'")
                    self.game_process.sendline('yes')
                    # Wait for the result after overwrite confirmation
                    self.game_process.expect('>', timeout=10)
                elif overwrite_idx == 1:  # Found prompt directly (no overwrite needed)
                    pass  # Already at prompt
                else:  # Timeout - assume no overwrite needed
                    pass
            except pexpect.TIMEOUT:
                # No overwrite prompt, continue
                pass
            
            # Get the final result
            result = self.game_process.before
            self._debug(f"Restore result: {result}")
            
            # Send LOOK to get current state
            self.game_process.sendline('LOOK')
            self.game_process.expect('>', timeout=5)
            game_state = self.game_process.before.strip()
            
            print(f"{self.GREEN}✓ Game restored{self.RESET}")
            return game_state
            
        except pexpect.TIMEOUT as e:
            print(f"\n{self.YELLOW}⚠️  Timeout during restore{self.RESET}")
            self._debug(f"Timeout detail: {e}")
            return False
        except Exception as e:
            self._debug(f"Restore error: {e}")
            return False
    
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
        
        # Load previous learning
        learning_loaded = self.load_learning()
        if learning_loaded:
            print(f"\n{self.CYAN}📚 Loaded previous learning: {len(self.learned_facts)} facts, {len(self.location_insights)} locations, {len(self.item_insights)} items{self.RESET}")
        
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
            
            # Check for quit - allow it if we're at max_turns or if AI is dead (ghost world)
            if command.upper() in ['QUIT', 'Q']:
                # Check if AI is in ghost world (dead) by looking for "passes through" in recent output
                is_dead = "passes through" in game_output.lower() or "ghost" in game_output.lower()
                
                if turn >= self.max_turns or is_dead:
                    if is_dead:
                        print("\nAI is dead (ghost world) - allowing quit to restart.")
                    else:
                        print("\nAI decided to quit the game (reached max turns).")
                    if self.auto_save:
                        self.save_game()  # Don't need return value here
                    break
                else:
                    print(f"\n{self.YELLOW}⚠️  AI tried to quit early (turn {turn}/{self.max_turns}), continuing...{self.RESET}")
                    # Convert QUIT to a different command to keep the game going
                    command = "LOOK"  # Safe command that won't break the game
            
            # Send command to game
            game_output = self.send_command(command)
            print(f"\n{self.YELLOW}{self.BOLD}📜 Game Response:{self.RESET}")
            print(f"{self.YELLOW}{game_output}{self.RESET}")
            
            # Handle RESTART confirmation
            if command.upper() == 'RESTART' and "Are you sure you want to restart?" in game_output:
                print(f"\n{self.CYAN}🤖 AI Command:{self.RESET} {self.CYAN}yes{self.RESET}")
                confirmation_output = self.send_command("yes")
                print(f"\n{self.YELLOW}{self.BOLD}📜 Game Response:{self.RESET}")
                print(f"{self.YELLOW}{confirmation_output}{self.RESET}")
                game_output = confirmation_output
            
            # Extract learning from this interaction
            self.extract_learning(game_output, command, game_output)
            
            # Check if we got empty output (possible timeout issue)
            if not game_output.strip():
                print(f"\n{self.YELLOW}⚠️  Warning: Got empty response{self.RESET}")
                game_output = "The game did not respond."
            
            # Don't automatically end - let max_turns or AI's QUIT command handle it
            # (Previously was checking for "quit" which gave false positives on words like "antiquity")
            
            # Auto-save every 10 turns
            if self.auto_save and turn % 10 == 0:
                save_success, new_state = self.save_game()
                # Save learning data
                self.save_learning()
                # Update game_output with fresh state after save
                if new_state:
                    game_output = new_state
                    self._debug("Game state refreshed after autosave")
            
            # Small delay between turns
            time.sleep(0.5)
        
        # Final save before exit
        if self.auto_save and self.turn_count > 0:
            print(f"\n{self.CYAN}Saving final game state...{self.RESET}")
            self.save_game()  # Don't need return value here
            self.save_learning()  # Save final learning data
        
        # Clean up
        if self.game_process and self.game_process.isalive():
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
        import subprocess
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
