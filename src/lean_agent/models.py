"""One request per step. Fixture responses never call a model; no automatic retries."""
from decimal import Decimal, InvalidOperation
import json
import os
import hashlib
from pathlib import Path
import time
from urllib import error, request

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


def payload(messages, model):
    result = {"model": model.get("id", "fixture-v1"), "messages": messages,
              "max_tokens": model.get("max_tokens", 1024), "temperature": model.get("temperature", 0),
              "stream": False, "response_format": {"type": "json_object"}}
    if model["backend"] == "openrouter":
        result["provider"] = {"only": [model["provider"]], "allow_fallbacks": False,
                              "require_parameters": True}
        if "seed" in model:
            result["seed"] = model["seed"]
    return result


def query(body, model, step, fixtures=None):
    if model["backend"] == "external":
        # A live rendezvous, not precomputed fixture playback. Each reply must
        # bind to the exact request, which includes the preceding Lean feedback.
        folder = Path(model["exchange_directory"]) / f"{step:03}"
        folder.mkdir(parents=True, exist_ok=False)
        serialized = json.dumps(body, ensure_ascii=False, sort_keys=True).encode()
        digest = hashlib.sha256(serialized).hexdigest()
        packet = {"request_sha256": digest, "request": body}
        temporary = folder / "request.tmp"
        temporary.write_text(json.dumps(packet, ensure_ascii=False, indent=2))
        temporary.rename(folder / "request.json")
        deadline = time.monotonic() + model["timeout_seconds"]
        while not (folder / "reply.json").exists():
            if time.monotonic() >= deadline:
                return {"transport_error": "ExternalReplyTimeout", "usage": {"cost": 0}}
            time.sleep(0.25)
        reply = json.loads((folder / "reply.json").read_text())
        if reply.get("request_sha256") != digest:
            return {"transport_error": "ExternalReplyRequestMismatch", "usage": {"cost": 0}}
        return {"id": f"external-{digest}", "model": model["id"], "provider": "conversation-relay",
                "choices": [{"message": {"role": "assistant", "content": reply.get("content")}}],
                "usage": {"cost": 0}, "external_request_sha256": digest,
                "cost_note": "No API charged by this harness; conversation token usage is unmeasured."}
    if model["backend"] == "fixture":
        return {"id": f"fixture-{step}", "model": "fixture-v1", "provider": "fixture",
                "choices": [{"message": {"role": "assistant", "content": fixtures[step - 1]}}],
                "usage": {"cost": 0, "prompt_tokens": 0, "completion_tokens": 0}}
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("Export OPENROUTER_API_KEY; .env files are not loaded automatically")
    call = request.Request(ENDPOINT, data=json.dumps(body, ensure_ascii=False).encode(),
                           headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    try:
        # Disable redirects so the Authorization header cannot follow another origin.
        class NoRedirect(request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        with request.build_opener(NoRedirect).open(call, timeout=model["timeout_seconds"]) as response:
            return json.loads(response.read())
    except (error.URLError, TimeoutError, OSError, ValueError) as exc:
        # No retry: a missing response may still represent a billed request.
        # Never serialize exception text or request headers containing credentials.
        return {"transport_error": type(exc).__name__, "http_status": getattr(exc, "code", None)}


def receipt(raw):
    """Unknown billing is explicit, never silently converted to zero."""
    raw = raw if isinstance(raw, dict) else {}
    usage = raw.get("usage", {})
    cost = usage.get("cost") if isinstance(usage, dict) else None
    try:
        if isinstance(cost, bool) or cost is None:
            raise ValueError()
        amount = Decimal(str(cost))
        if not amount.is_finite() or amount < 0:
            raise ValueError()
        billed = str(amount)
    except (InvalidOperation, ValueError):
        billed = None
    content = None
    try:
        content = raw["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        pass
    return {"content": content if isinstance(content, str) else None,
            "cost_usd": billed, "usage": usage,
            "id": raw.get("id"), "model": raw.get("model"), "provider": raw.get("provider")}
