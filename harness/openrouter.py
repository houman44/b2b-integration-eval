"""Minimal OpenRouter client (standard library HTTP; python-dotenv for the key).

The API key is read from .env by python-dotenv and only ever placed in the
Authorization header. It is never printed, logged or written to disk;
redact() is applied to everything the harness writes.
"""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://openrouter.ai/api/v1"
ROOT = Path(__file__).resolve().parent.parent
APP_HEADERS = {"X-Title": "b2b-integration-eval"}


class SetupError(RuntimeError):
    pass


def load_key() -> str:
    try:
        from dotenv import load_dotenv
    except ImportError as e:
        raise SetupError("python-dotenv is not installed: pip install -r requirements.txt") from e
    load_dotenv(ROOT / ".env", override=False)
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise SetupError("OPENROUTER_API_KEY is not set (create .env from .env.example)")
    return key


def redact(text: str, key: str) -> str:
    return text.replace(key, "[REDACTED]") if key else text


def _request(method, path, key=None, body=None, timeout=60):
    headers = {"Content-Type": "application/json", **APP_HEADERS}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8")), time.time() - t0
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw[:2000]}
        return e.code, payload, time.time() - t0
    except (urllib.error.URLError, TimeoutError, OSError) as e:   # timeouts, resets
        return 0, {"error": {"message": f"{type(e).__name__}: {e}"}}, time.time() - t0


def list_models():
    """Public endpoint, no key needed."""
    status, payload, _ = _request("GET", "/models")
    if status != 200:
        raise SetupError(f"GET /models returned HTTP {status}")
    return {m["id"]: m for m in payload["data"]}


def key_info(key):
    """GET /key: limits and usage for this key. Costs nothing."""
    return _request("GET", "/key", key=key)


def chat(key, model, prompt, *, temperature, max_tokens, seed=None, timeout=900, retries=3):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        # Only route to providers that do not store or train on prompts.
        "provider": {"data_collection": "deny"},
    }
    if seed is not None:
        body["seed"] = seed
    attempts = []
    for i in range(retries + 1):
        status, payload, latency = _request("POST", "/chat/completions", key=key, body=body,
                                            timeout=timeout)
        attempts.append({"status": status, "latency_s": round(latency, 3)})
        if status == 200 and "choices" in payload:
            break
        if status not in (429, 500, 502, 503) or i == retries:   # no retry on timeouts: avoid double billing
            break
        time.sleep(min(60, 5 * 2 ** i))
    return body, status, payload, attempts


def chat_raw(key, body, timeout=900, retries=4):
    """One request with a caller-built body (used by the agentic harness).
    Retries 429 (rate limit) and 5xx answers with back-off."""
    body = {**body, "provider": {"data_collection": "deny"}}
    for i in range(retries + 1):
        status, payload, latency = _request("POST", "/chat/completions", key=key, body=body,
                                            timeout=timeout)
        if status not in (429, 500, 502, 503) or i == retries:
            return status, payload, latency
        time.sleep(min(60, 8 * 2 ** i))
