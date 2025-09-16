import json
import os
from datetime import datetime, timezone
from typing import Dict, Optional


class StateStore:
	"""File-based state to track last-run timestamps per account.

	Stored at: {state_dir}/state.json
	Schema:
	{
		"accounts": {
			"gmail": {"last_run_iso": "..."},
			"outlook": {"last_run_iso": "..."}
		}
	}
	"""

	def __init__(self, state_dir: str) -> None:
		self.state_dir = state_dir
		self.state_file = os.path.join(state_dir, "state.json")
		os.makedirs(state_dir, exist_ok=True)
		self._state: Dict[str, Dict] = {"accounts": {}}
		self._load()

	def _load(self) -> None:
		if not os.path.exists(self.state_file):
			return
		try:
			with open(self.state_file, "r", encoding="utf-8") as f:
				self._state = json.load(f)
		except Exception:
			# Corrupt state: reset
			self._state = {"accounts": {}}

	def save(self) -> None:
		tmp_path = self.state_file + ".tmp"
		with open(tmp_path, "w", encoding="utf-8") as f:
			json.dump(self._state, f, indent=2)
		os.replace(tmp_path, self.state_file)

	def get_last_run(self, account_key: str) -> Optional[datetime]:
		node = self._state.get("accounts", {}).get(account_key)
		if not node:
			return None
		iso = node.get("last_run_iso")
		if not iso:
			return None
		try:
			return datetime.fromisoformat(iso)
		except Exception:
			return None

	def set_last_run(self, account_key: str, dt: Optional[datetime] = None) -> None:
		if dt is None:
			dt = datetime.now(timezone.utc)
		self._state.setdefault("accounts", {}).setdefault(account_key, {})[
			"last_run_iso"
		] = dt.astimezone(timezone.utc).isoformat()
		self.save()
