#!/bin/bash

# File: start.sh
# Description: Startup script for JZFileBrowser
# Author: Your Name
# Version: 1.0

# Set colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Display header
echo -e "${GREEN}"
echo "   ___  _______  ___  ___  _______  ___       ___  ___  ___  __   __  ___  "
echo "  |   ||   _   ||   ||   ||   _   ||   |     |   ||   ||   ||  | |  ||   | "
echo "  |   ||  |_|  ||   ||   ||  |_|  ||   |_____|   ||   ||   ||  |_|  ||   | "
echo "  |   ||       ||   ||   ||       ||   |_____|   ||   ||   ||       ||   | "
echo "  |   ||       ||   ||   ||       ||    ___ |   ||   ||   ||       ||   | "
echo "  |   ||   _   ||   ||   ||   _   ||   |   ||   ||   ||   | |     | |   | "
echo "  |___||__| |__||___||___||__| |__||___|   ||___||___||___|  |___|  |___| "
echo -e "${NC}"
echo "Modern File Browser - Version 1.0"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null
then
    echo -e "${RED}Python 3 could not be found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creating Python virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    
    echo -e "${BLUE}Installing dependencies...${NC}"
    pip install --upgrade pip
    pip install flask werkzeug
    
    deactivate
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Create required directories
mkdir -p files
mkdir -p app/static/css
mkdir -p app/static/img
mkdir -p app/templates

# Check if config file exists
if [ ! -f "config.txt" ]; then
    echo -e "${BLUE}Creating default config file...${NC}"
    echo "$(pwd)/files" > config.txt
fi

# Run the application
echo -e "${GREEN}"
echo "Starting JZFileBrowser..."
echo -e "Access at: ${BLUE}http://localhost:5000${GREEN}"
echo "Press Ctrl+C to stop"
echo -e "${NC}"
python3 app/main.py

# Deactivate virtual environment when done
deactivate
