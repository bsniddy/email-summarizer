# Email Summarizer

A Python tool that fetches emails from Gmail and Outlook, parses attachments, and generates daily summaries using a local Ollama model.

## Features

- **Multi-provider support**: Gmail and Outlook via IMAP
- **Attachment parsing**: PDF, DOCX, CSV, TXT, HTML files
- **Smart importance detection**: Keywords, attachments, known contacts
- **Local AI summarization**: Uses Ollama for privacy
- **Flexible scheduling**: Since last run or 24-hour windows
- **macOS integration**: LaunchAgent for nightly runs

## Prerequisites

1. **Python 3.8+**
2. **Ollama installed and running**:
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull the model (adjust as needed)
   ollama pull llama3.1:8b
   ```

3. **Email app passwords**:
   - Gmail: Enable 2FA and create an app password
   - Outlook: Use app password or enable "Less secure app access"

## Installation

1. **Clone and install**:
   ```bash
   cd /Users/brodysnyder/Documents/Projects/email-summarizer
   pip install -e .
   ```

2. **Set up environment variables**:
   ```bash
   # Add to ~/.zshrc or ~/.bash_profile
   export GMAIL_USERNAME="your-email@gmail.com"
   export GMAIL_PASSWORD="your-app-password"
   export OUTLOOK_USERNAME="your-email@outlook.com"
   export OUTLOOK_PASSWORD="your-app-password"
   export OLLAMA_MODEL="llama3.1:8b"  # Optional
   ```

3. **Create logs directory**:
   ```bash
   mkdir -p /Users/brodysnyder/Documents/Projects/email-summarizer/logs
   ```

## Usage

### Command Line

```bash
# Basic usage (since last run)
email-summarizer

# Last 24 hours
email-summarizer --24h

# Gmail only
email-summarizer --gmail-only

# Outlook only  
email-summarizer --outlook-only

# Exclude spam folders
email-summarizer --no-spam

# Save to file
email-summarizer --output daily-digest.md
```

### Nightly Automation (macOS)

1. **Install the LaunchAgent**:
   ```bash
   # Copy the plist to LaunchAgents
   cp com.brodysnyder.email-summarizer.plist ~/Library/LaunchAgents/
   
   # Load and start the service
   launchctl load ~/Library/LaunchAgents/com.brodysnyder.email-summarizer.plist
   launchctl start com.brodysnyder.email-summarizer
   ```

2. **Check status**:
   ```bash
   launchctl list | grep email-summarizer
   ```

3. **View logs**:
   ```bash
   tail -f /Users/brodysnyder/Documents/Projects/email-summarizer/logs/email-summarizer.log
   ```

4. **Stop/remove**:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.brodysnyder.email-summarizer.plist
   rm ~/Library/LaunchAgents/com.brodysnyder.email-summarizer.plist
   ```

## Configuration

### Email Accounts

The tool automatically detects configured accounts via environment variables:

- `GMAIL_USERNAME` / `GMAIL_PASSWORD`
- `OUTLOOK_USERNAME` / `OUTLOOK_PASSWORD`

### Importance Detection

Emails are marked as important if they contain:
- High-priority keywords: urgent, asap, deadline, important, etc.
- Attachments
- From known domains (customize in `summarizer.py`)
- Reply/forward threads

### State Management

Last run timestamps are stored in `~/.email-summarizer/state.json` to avoid reprocessing emails.

## Output Format

The tool generates Markdown digests with:

- **Header**: Date, total emails, important count
- **Important Emails**: Highlighted with 🔥, detailed summaries
- **Other Emails**: Regular emails with bullet summaries
- **Attachments**: Parsed and included in summaries

## Troubleshooting

### Common Issues

1. **IMAP authentication fails**:
   - Verify app passwords are correct
   - Check 2FA is enabled for Gmail
   - Ensure "Less secure app access" is enabled for Outlook

2. **Ollama connection fails**:
   - Ensure Ollama is running: `ollama serve`
   - Check model is installed: `ollama list`
   - Verify model name in environment variables

3. **No emails found**:
   - Check if emails exist in the time window
   - Verify spam folder inclusion settings
   - Check IMAP folder permissions

### Logs

- **Success logs**: `/Users/brodysnyder/Documents/Projects/email-summarizer/logs/email-summarizer.log`
- **Error logs**: `/Users/brodysnyder/Documents/Projects/email-summarizer/logs/email-summarizer-error.log`

### Manual Testing

```bash
# Test with 24h window
python3 src/email_summarizer/cli.py --24h --output test-digest.md

# Test Gmail only
python3 src/email_summarizer/cli.py --gmail-only --24h
```

## Security Notes

- App passwords are stored in environment variables
- No email content is stored permanently (only last run timestamps)
- All processing happens locally with Ollama
- IMAP connections use SSL/TLS

## Customization

- **Importance rules**: Edit `is_important()` in `summarizer.py`
- **Known domains**: Update `known_domains` list in `summarizer.py`
- **Ollama model**: Change `OLLAMA_MODEL` environment variable
- **Schedule time**: Modify `Hour`/`Minute` in the plist file
