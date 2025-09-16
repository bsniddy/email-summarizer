import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class EmailAccountConfig:
	provider: str  # "gmail" or "outlook"
	imap_host: str
	imap_port: int = 993
	username: str = ""
	password: str = ""  # Prefer app password if available
	use_ssl: bool = True


@dataclass
class AppConfig:
	gmail: Optional[EmailAccountConfig]
	outlook: Optional[EmailAccountConfig]
	ollama_model: str = "llama3.1:8b"
	state_dir: str = os.path.expanduser("~/.email-summarizer")
	include_spam: bool = True


def load_config_from_env() -> AppConfig:
	# Load from ~/.email-summarizer/config.env if present
	"""Load configuration from environment variables.

	Expected env vars:
	- GMAIL_USERNAME, GMAIL_PASSWORD (or app password)
	- OUTLOOK_USERNAME, OUTLOOK_PASSWORD
	- OLLAMA_MODEL (optional)
	- EMAIL_SUMMARIZER_STATE_DIR (optional)
	"""
	load_path = os.path.expanduser("~/.email-summarizer/config.env")
	if os.path.exists(load_path):
		with open(load_path, "r", encoding="utf-8") as f:
			for line in f:
				line=line.strip()
				if not line or line.startswith("#") or "=" not in line:
					continue
				key, val = line.split("=", 1)
				os.environ.setdefault(key.strip(), val.strip())

	gmail_user = os.getenv("GMAIL_USERNAME", "").strip()
	gmail_pass = os.getenv("GMAIL_PASSWORD", "").strip()

	outlook_user = os.getenv("OUTLOOK_USERNAME", "").strip()
	outlook_pass = os.getenv("OUTLOOK_PASSWORD", "").strip()

	ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b").strip() or "llama3.1:8b"
	state_dir = os.getenv("EMAIL_SUMMARIZER_STATE_DIR", os.path.expanduser("~/.email-summarizer")).strip()

	gmail = None
	if gmail_user and gmail_pass:
		gmail = EmailAccountConfig(
			provider="gmail",
			imap_host="imap.gmail.com",
			username=gmail_user,
			password=gmail_pass,
		)

	outlook = None
	if outlook_user and outlook_pass:
		outlook = EmailAccountConfig(
			provider="outlook",
			imap_host="outlook.office365.com",
			username=outlook_user,
			password=outlook_pass,
		)

	return AppConfig(
		gmail=gmail,
		outlook=outlook,
		ollama_model=ollama_model,
		state_dir=state_dir,
	)
