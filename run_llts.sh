#!/bin/bash

# Bash script to run the signal recording application

# Navigate to the project directory
cd /path/to/CKJAPAN-LLTS

# Ensure script is run with bash
if [ -z "$BASH_VERSION" ]; then
    exec bash "$0" "$@"
fi

# Color codes for formatting output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if virtual environment exists
VENV_PATH=".venv"

# Function to create and activate virtual environment
setup_venv() {
    echo -e "${YELLOW}Setting up virtual environment...${NC}"
    
    # Check if virtualenv is installed
    if ! command -v virtualenv &> /dev/null; then
        echo -e "${RED}virtualenv is not installed. Installing...${NC}"
        pip install virtualenv
    fi

    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_PATH" ]; then
        virtualenv "$VENV_PATH"
    fi

    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
}

# Function to install dependencies
install_dependencies() {
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
}

# Function to run the signal recorder
run_recorder() {
    echo -e "${GREEN}Starting Signal Recorder...${NC}"
    python main.py
}

# Main script execution
main() {
    # Check if config file exists
    if [ ! -f "config.yaml" ]; then
        echo -e "${RED}Error: config.yaml not found. Please create the configuration file.${NC}"
        exit 1
    fi

    # Setup virtual environment
    setup_venv

    # Install dependencies
    install_dependencies

    # Run the recorder
    run_recorder

    # Deactivate virtual environment when done
    deactivate
}

# Trap Ctrl+C to ensure clean exit
trap 'echo -e "\n${RED}Interrupted. Exiting...${NC}"; exit 1' INT

# Run main function
main