"""Optional provider boundary for structured LLM calls.

The core agent does not require this module to run. Configuration is read from
process environment variables; secrets are never stored in source or traces.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class LLMResult:
    status: str
    value: dict[str, Any] | None = None
    model: str = ""
    error: str = ""


class ConfiguredLLM:
    def __init__(self, *, endpoint: str | None = None, api_key: str | None = None, model: str | None = None, timeout: float = 30.0) -> None:
        self.endpoint = endpoint or os.getenv("HIVER_LLM_ENDPOINT", "")
        self.api_key = api_key or os.getenv("HIVER_LLM_API_KEY", "")
        self.model = model or os.getenv("HIVER_LLM_MODEL", "")
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self.endpoint and self.api_key and self.model)

    def structured_json(self, system: str, user: str) -> LLMResult:
        if not self.available:
            return LLMResult("NOT_AVAILABLE", model=self.model, error="LLM provider is not configured")
        payload = json.dumps({"model": self.model, "response_format": {"type": "json_object"}, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}).encode("utf-8")
        request = Request(self.endpoint, data=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}, method="POST")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
            value = body.get("choices", [{}])[0].get("message", {}).get("content", body)
            if isinstance(value, str):
                value = json.loads(value)
            if not isinstance(value, dict):
                return LLMResult("INVALID", model=self.model, error="provider response was not a JSON object")
            return LLMResult("OK", value=value, model=self.model)
        except Exception as exc:  # Provider failures must not crash deterministic runs.
            return LLMResult("ERROR", model=self.model, error=type(exc).__name__)
