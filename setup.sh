#!/bin/bash
# Setup script for Zork AI Player

set -e

echo "Setting up Zork AI Player..."

# Create directory structure
BASE_DIR=~/gudlyf/src/zork_ai
echo "Creating directory: $BASE_DIR"
mkdir -p "$BASE_DIR/games"
cd "$BASE_DIR"

# Check if Frotz is installed
if ! command -v dfrotz &> /dev/null; then
    echo "Frotz not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Installing via Homebrew..."
        brew install frotz
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Please install frotz manually:"
        echo "  Ubuntu/Debian: sudo apt-get install frotz"
        echo "  Fedora: sudo dnf install frotz"
        echo "  Arch: sudo pacman -S frotz"
        exit 1
    fi
fi

echo "Frotz installed: $(which dfrotz)"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install anthropic

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "WARNING: ANTHROPIC_API_KEY not set!"
    echo "Please set your API key:"
    echo "  export ANTHROPIC_API_KEY='your-api-key-here'"
    echo ""
fi

# Download Zork if not present
if [ ! -f "games/zork1.z5" ]; then
    echo ""
    echo "Zork I game file not found."
    echo "Please download it manually from one of these sources:"
    echo "  - https://ifdb.org/viewgame?id=4gxk83ja4twckm6j"
    echo "  - http://www.ifarchive.org/indexes/if-archiveXgamesXzcode.html"
    echo ""
    echo "Save it as: $BASE_DIR/games/zork1.z5"
    echo ""
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment: source $BASE_DIR/venv/bin/activate"
echo "  2. Set your API key: export ANTHROPIC_API_KEY='your-key'"
echo "  3. Download Zork and save to: $BASE_DIR/games/zork1.z5"
echo "  4. Run: python zork_ai_player.py games/zork1.z5"
echo ""
