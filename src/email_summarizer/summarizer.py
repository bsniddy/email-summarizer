import json
import requests
from typing import List, Dict, Any
from .imap_fetcher import FetchedEmail
from .attachment_parser import parse_all_attachments


class EmailSummarizer:
    def __init__(self, ollama_model: str = "llama3.1:8b", ollama_url: str = "http://localhost:11434"):
        self.ollama_model = ollama_model
        self.ollama_url = ollama_url
    
    def _call_ollama(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call Ollama API with the given prompt."""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.3
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
        except Exception as e:
            print(f"Ollama API error: {e}")
            return ""
    
    def is_important(self, email: FetchedEmail) -> bool:
        """Determine if an email is important based on heuristics."""
        subject = email.subject.lower()
        from_addr = email.from_addr.lower()
        
        # High importance indicators
        high_priority_keywords = [
            'urgent', 'asap', 'immediately', 'deadline', 'important',
            'action required', 'response needed', 'meeting', 'call',
            'emergency', 'critical', 'priority'
        ]
        
        # Check subject for high priority keywords
        if any(keyword in subject for keyword in high_priority_keywords):
            return True
        
        # Check if from known contacts (simplified - you could expand this)
        known_domains = ['company.com', 'workplace.org']  # Add your important domains
        if any(domain in from_addr for domain in known_domains):
            return True
        
        # Check if email has attachments (often indicates importance)
        if email.attachments:
            return True
        
        # Check if email is a reply (conversation thread)
        if subject.startswith('re:') or subject.startswith('fwd:'):
            return True
        
        return False
    
    def summarize_email(self, email: FetchedEmail) -> str:
        """Generate a summary for a single email."""
        # Parse attachments
        parsed_attachments = parse_all_attachments(email.attachments)
        attachment_text = ""
        if parsed_attachments:
            attachment_summaries = []
            for filename, text in parsed_attachments:
                # Truncate very long attachments
                if len(text) > 1000:
                    text = text[:1000] + "..."
                attachment_summaries.append(f"Attachment '{filename}': {text}")
            attachment_text = "\n".join(attachment_summaries)
        
        # Prepare content for summarization
        content_parts = []
        if email.body_text:
            content_parts.append(f"Email body: {email.body_text}")
        if attachment_text:
            content_parts.append(f"Attachments: {attachment_text}")
        
        if not content_parts:
            return f"Email from {email.from_addr} with subject '{email.subject}' (no readable content)"
        
        content = "\n\n".join(content_parts)
        
        # Truncate very long content
        if len(content) > 3000:
            content = content[:3000] + "..."
        
        prompt = f"""Summarize this email in 2-3 bullet points. Focus on key information, actions needed, and important details.

From: {email.from_addr}
Subject: {email.subject}
Date: {email.date}

Content:
{content}

Summary:"""
        
        summary = self._call_ollama(prompt, max_tokens=200)
        if not summary:
            # Fallback summary
            summary = f"• From: {email.from_addr}\n• Subject: {email.subject}\n• Content: {email.body_text[:200]}..."
        
        return summary
    
    def generate_daily_digest(self, emails: List[FetchedEmail]) -> str:
        """Generate a daily digest of all emails."""
        if not emails:
            return "No emails found for the specified time period."
        
        # Separate important and regular emails
        important_emails = [e for e in emails if self.is_important(e)]
        regular_emails = [e for e in emails if not self.is_important(e)]
        
        digest_parts = []
        
        # Header
        digest_parts.append(f"# Daily Email Digest - {emails[0].date.strftime('%Y-%m-%d')}")
        digest_parts.append(f"Total emails: {len(emails)}")
        digest_parts.append(f"Important emails: {len(important_emails)}")
        digest_parts.append("")
        
        # Important emails section
        if important_emails:
            digest_parts.append("## 🔥 Important Emails")
            digest_parts.append("")
            for email in important_emails:
                summary = self.summarize_email(email)
                digest_parts.append(f"**From:** {email.from_addr}")
                digest_parts.append(f"**Subject:** {email.subject}")
                digest_parts.append(f"**Time:** {email.date.strftime('%H:%M')}")
                digest_parts.append("")
                digest_parts.append(summary)
                digest_parts.append("---")
                digest_parts.append("")
        
        # Regular emails section
        if regular_emails:
            digest_parts.append("## 📧 Other Emails")
            digest_parts.append("")
            for email in regular_emails:
                summary = self.summarize_email(email)
                digest_parts.append(f"**From:** {email.from_addr}")
                digest_parts.append(f"**Subject:** {email.subject}")
                digest_parts.append(f"**Time:** {email.date.strftime('%H:%M')}")
                digest_parts.append("")
                digest_parts.append(summary)
                digest_parts.append("---")
                digest_parts.append("")
        
        return "\n".join(digest_parts)
