#!/usr/bin/env python3

import sys
import os
from datetime import datetime
from typing import List

import click

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from email_summarizer.config import load_config_from_env
from email_summarizer.state import StateStore
from email_summarizer.imap_fetcher import IMAPEmailFetcher
from email_summarizer.summarizer import EmailSummarizer


def fetch_emails_from_account(account_config, state_store: StateStore, window_24h: bool, include_spam: bool) -> List:
    """Fetch emails from a single account."""
    fetcher = IMAPEmailFetcher(
        host=account_config.imap_host,
        username=account_config.username,
        password=account_config.password,
        use_ssl=account_config.use_ssl,
        account_key=account_config.provider
    )
    
    last_run = state_store.get_last_run(account_config.provider)
    emails = fetcher.fetch(last_run, window_24h, include_spam)
    
    # Update last run time
    state_store.set_last_run(account_config.provider)
    
    return emails


@click.command()
@click.option('--24h', 'window_24h', is_flag=True, help='Fetch emails from last 24 hours instead of since last run')
@click.option('--gmail-only', is_flag=True, help='Only process Gmail account')
@click.option('--outlook-only', is_flag=True, help='Only process Outlook account')
@click.option('--no-spam', is_flag=True, help='Exclude spam/junk folders')
@click.option('--output', '-o', help='Output file path (default: print to stdout)')
def main(window_24h: bool, gmail_only: bool, outlook_only: bool, no_spam: bool, output: str):
    """Email Summarizer - Fetch and summarize emails from Gmail and Outlook."""
    
    try:
        # Load configuration
        config = load_config_from_env()
        
        if not config.gmail and not config.outlook:
            click.echo("Error: No email accounts configured. Set GMAIL_USERNAME/GMAIL_PASSWORD and/or OUTLOOK_USERNAME/OUTLOOK_PASSWORD environment variables.", err=True)
            sys.exit(1)
        
        # Initialize state store
        state_store = StateStore(config.state_dir)
        
        # Initialize summarizer
        summarizer = EmailSummarizer(config.ollama_model)
        
        # Collect all emails
        all_emails = []
        
        if config.gmail and not outlook_only:
            click.echo("Fetching emails from Gmail...")
            gmail_emails = fetch_emails_from_account(
                config.gmail, state_store, window_24h, not no_spam
            )
            all_emails.extend(gmail_emails)
            click.echo(f"Found {len(gmail_emails)} emails from Gmail")
        
        if config.outlook and not outlook_only:
            click.echo("Fetching emails from Outlook...")
            outlook_emails = fetch_emails_from_account(
                config.outlook, state_store, window_24h, not no_spam
            )
            all_emails.extend(outlook_emails)
            click.echo(f"Found {len(outlook_emails)} emails from Outlook")
        
        if not all_emails:
            click.echo("No emails found for the specified time period.")
            return
        
        # Generate digest
        click.echo("Generating digest...")
        digest = summarizer.generate_daily_digest(all_emails)
        
        # Output result
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(digest)
            click.echo(f"Digest saved to {output}")
        else:
            click.echo(digest)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
