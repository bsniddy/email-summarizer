from __future__ import annotations

import email
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from IMAPClient import IMAPClient


@dataclass
class FetchedEmail:
	account: str
	uid: int
	subject: str
	from_addr: str
	to_addrs: List[str]
	date: datetime
	body_text: str
	html_text: Optional[str]
	attachments: List[Tuple[str, bytes, str]]  # (filename, content, mime)
	raw_message: bytes


class IMAPEmailFetcher:
	def __init__(self, host: str, username: str, password: str, use_ssl: bool = True, account_key: str = "") -> None:
		self.host = host
		self.username = username
		self.password = password
		self.use_ssl = use_ssl
		self.account_key = account_key or username

	def _connect(self) -> IMAPClient:
		client = IMAPClient(self.host, use_uid=True, ssl=self.use_ssl)
		client.login(self.username, self.password)
		return client

	def _search_since(self, client: IMAPClient, since_dt: Optional[datetime], include_spam: bool) -> List[int]:
		uids: List[int] = []
		mailboxes: List[bytes] = [b"INBOX"]
		if include_spam:
			# Common spam/junk folders across providers
			mailboxes += [b"[Gmail]/Spam", b"Junk", b"Spam"]
		for mbox in mailboxes:
			try:
				client.select_folder(mbox, readonly=True)
			except Exception:
				continue
			if since_dt:
				criteria = ["SINCE", since_dt.strftime("%d-%b-%Y")]
			else:
				criteria = ["ALL"]
			try:
				found = client.search(criteria)
			except Exception:
				found = []
			if found:
				uids.extend(found)
		# Deduplicate
		return sorted(list(set(uids)))

	def fetch(self, last_run: Optional[datetime], window_24h: bool, include_spam: bool = True) -> List[FetchedEmail]:
		"""Fetch emails since last_run, or last 24h if window_24h is True.
		Includes spam/junk if include_spam.
		"""
		since_dt: Optional[datetime] = None
		if window_24h:
			since_dt = datetime.now(timezone.utc) - timedelta(days=1)
		elif last_run:
			since_dt = last_run.astimezone(timezone.utc)

		with self._connect() as client:
			uid_list = self._search_since(client, since_dt, include_spam)
			if not uid_list:
				return []
			messages = client.fetch(uid_list, [
				b'ENVELOPE', b'RFC822', b'BODYSTRUCTURE'
			])

	emails: List[FetchedEmail] = []
	for uid, data in messages.items():
		try:
			raw = data[b'RFC822']
			msg = email.message_from_bytes(raw)

			# Extract basic fields
			subject = msg.get('Subject', '')
			from_addr = msg.get('From', '')
			to_addrs = [addr.strip() for addr in msg.get('To', '').split(',') if addr.strip()]
			date_str = msg.get('Date', '')
                
			# Parse date
			try:
				from email.utils import parsedate_to_datetime
				date = parsedate_to_datetime(date_str)
			except Exception:
				date = datetime.now(timezone.utc)

			# Extract body text and HTML
			body_text = ""
			html_text = None
			attachments: List[Tuple[str, bytes, str]] = []

			if msg.is_multipart():
				for part in msg.walk():
					content_type = part.get_content_type()
					content_disposition = str(part.get('Content-Disposition', ''))
					
					if 'attachment' in content_disposition:
					    # Handle attachments
					    filename = part.get_filename()
					    if filename:
					        payload = part.get_payload(decode=True)
					        if payload:
					            attachments.append((filename, payload, content_type))
					elif content_type == 'text/plain' and not body_text:
					    # Plain text body
					    payload = part.get_payload(decode=True)
					    if payload:
					        try:
					            body_text = payload.decode('utf-8', errors='ignore').strip()
					        except Exception:
					            body_text = str(payload).strip()
					elif content_type == 'text/html' and not html_text:
					    # HTML body
					    payload = part.get_payload(decode=True)
					    if payload:
					        try:
					            html_text = payload.decode('utf-8', errors='ignore')
					        except Exception:
					            html_text = str(payload)
			else:
				# Single part message
				content_type = msg.get_content_type()
				payload = msg.get_payload(decode=True)
				if payload:
					try:
					    text = payload.decode('utf-8', errors='ignore')
					    if content_type == 'text/html':
					        html_text = text
					    else:
					        body_text = text.strip()
					except Exception:
					    text = str(payload)
					    if content_type == 'text/html':
					        html_text = text
					    else:
					        body_text = text.strip()

			emails.append(FetchedEmail(
                    account=self.account_key,
                    uid=int(uid),
                    subject=subject,
                    from_addr=from_addr,
                    to_addrs=to_addrs,
                    date=date,
                    body_text=body_text,
                    html_text=html_text,
                    attachments=attachments,
                    raw_message=raw,
			))
		except Exception as e:
			print(f"Error parsing email {uid}: {e}")
			continue
	return emails
