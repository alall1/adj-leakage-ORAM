# src/eval/io_utils.py
from __future__ import annotations
import json
import os
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List

def ensure_dir(path: str) -> None:
	os.makedirs(path, exist_ok=True)

def write_json(path: str, obj: Any) -> None:
	def default(o):
		if is_dataclass(o):
			return asdict(o)
		raise TypeError(f"Not JSON serializable: {type(o)}")
	with open(path, "w", encoding="utf-8") as f:
		json.dump(obj, f, indent=2, default=default)

def write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
	if not rows:
		with open(path, "w", encoding="utf-8") as f:
			f.write("")
		return

	headers = list(rows[0].keys())
	with open(path, "w", encoding="utf-8") as f:
		f.write(",".join(headers) + "\n")
		for r in rows:
			f.write(",".join(str(r.get(h, "")) for h in headers) + "\n")
