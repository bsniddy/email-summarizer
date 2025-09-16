#!/bin/bash

# Email Summarizer Installation Script

set -e

echo "Email Summarizer Installation Script"
echo "========================================"

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Python $PYTHON_VERSION found, but Python $REQUIRED_VERSION+ is required."
    exit 1
fi

echo "Python $PYTHON_VERSION found"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Ollama is not installed. Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "Ollama installed"
else
    echo "Ollama found"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -e .

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs

# Check for environment variables
echo "🔧 Checking configuration..."

if [ -z "$GMAIL_USERNAME" ] && [ -z "$OUTLOOK_USERNAME" ]; then
    echo "No email accounts configured."
    echo "Please set the following environment variables:"
    echo "  export GMAIL_USERNAME='your-email@gmail.com'"
    echo "  export GMAIL_PASSWORD='your-app-password'"
    echo "  export OUTLOOK_USERNAME='your-email@outlook.com'"
    echo "  export OUTLOOK_PASSWORD='your-app-password'"
    echo ""
    echo "Add these to your ~/.zshrc or ~/.bash_profile file."
fi

# Pull Ollama model
echo "Pulling Ollama model (llama3.1:8b)..."
ollama pull llama3.1:8b

# Install LaunchAgent
echo "Setting up nightly automation..."
cp com.brodysnyder.email-summarizer.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.brodysnyder.email-summarizer.plist

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Set up your email credentials (see above)"
echo "2. Test the tool: email-summarizer --24h"
echo "3. Check logs: tail -f logs/email-summarizer.log"
echo ""
echo "The tool will run automatically every night at 6:00 AM."
