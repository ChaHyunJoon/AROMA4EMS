"""Observability helpers for AROMA reward-refinement workflow.
observability: 관찰 가능성, logging: 기록, 
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

# 지정된 경로에 json 형식으로 데이터를 저장하는 함수
def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
