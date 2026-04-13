#!/usr/bin/env python3
"""Couche IA unifiee pour CryptoScanner."""

from __future__ import annotations

import os
import requests

GROQ_CHAT_URL    = "https://api.groq.com/openai/v1/chat/completions"
ANTHROPIC_URL    = "https://api.anthropic.com/v1/messages"
OPENAI_CHAT_URL  = "https://api.openai.com/v1/chat/completions"


def _pick_provider(user_keys: dict | None = None):
    user_keys = user_keys or {}
    env_pref = (os.environ.get("AI_PROVIDER") or "auto").strip().lower()
    groq_env      = os.environ.get("GROQ_API_KEY", "").strip()
    anthropic_env = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    openai_env    = os.environ.get("OPENAI_API_KEY", "").strip()
    groq_user      = (user_keys.get("groq") or "").strip()
    anthropic_user = (user_keys.get("anthropic") or user_keys.get("claude") or "").strip()
    openai_user    = (user_keys.get("openai") or "").strip()

    if env_pref == "groq"      and (groq_user or groq_env):         return "groq",      groq_user or groq_env
    if env_pref == "anthropic" and (anthropic_user or anthropic_env): return "anthropic", anthropic_user or anthropic_env
    if env_pref == "openai"    and (openai_user or openai_env):     return "openai",    openai_user or openai_env

    # Ordre priorité user > env : groq → anthropic → openai
    if groq_user:      return "groq",      groq_user
    if groq_env:       return "groq",      groq_env
    if anthropic_user: return "anthropic", anthropic_user
    if anthropic_env:  return "anthropic", anthropic_env
    if openai_user:    return "openai",    openai_user
    if openai_env:     return "openai",    openai_env
    return None, ""


def get_ai_status(user_keys: dict | None = None):
    provider, key = _pick_provider(user_keys)
    masked = ""
    if key:
        masked = key[:6] + "..." + key[-4:] if len(key) > 12 else "configuree"
    return {
        "provider": provider or "none",
        "configured": bool(key),
        "masked": masked,
    }


def analyze_text(prompt: str, system: str = "", max_tokens: int = 900, temperature: float = 0.35, user_keys: dict | None = None):
    provider, api_key = _pick_provider(user_keys)
    if not provider or not api_key:
        return {"ok": False, "error": "Aucun provider IA configure", "provider": "none"}

    if provider == "openai":
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            r = requests.post(
                OPENAI_CHAT_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens},
                timeout=45,
            )
            data = r.json()
            if r.status_code >= 400:
                return {"ok": False, "error": data.get("error", {}).get("message", f"OpenAI HTTP {r.status_code}"), "provider": provider}
            content = ((data.get("choices") or [{}])[0].get("message") or {}).get("content", "").strip()
            if not content:
                return {"ok": False, "error": "Reponse vide OpenAI", "provider": provider}
            return {"ok": True, "provider": provider, "analysis": content}
        except Exception as exc:
            return {"ok": False, "error": str(exc), "provider": provider}

    if provider == "groq":
        model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            r = requests.post(
                GROQ_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=45,
            )
            data = r.json()
            if r.status_code >= 400:
                return {"ok": False, "error": data.get("error", {}).get("message", f"Groq HTTP {r.status_code}"), "provider": provider}
            content = ((data.get("choices") or [{}])[0].get("message") or {}).get("content", "").strip()
            if not content:
                return {"ok": False, "error": "Reponse vide Groq", "provider": provider}
            return {"ok": True, "provider": provider, "analysis": content}
        except Exception as exc:
            return {"ok": False, "error": str(exc), "provider": provider}

    model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")
    content_blocks = []
    if system:
        content_blocks.append({"type": "text", "text": system + "\n\n" + prompt})
    else:
        content_blocks.append({"type": "text", "text": prompt})
    try:
        r = requests.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": content_blocks}],
            },
            timeout=45,
        )
        data = r.json()
        if r.status_code >= 400:
            return {"ok": False, "error": data.get("error", {}).get("message", f"Anthropic HTTP {r.status_code}"), "provider": provider}
        blocks = data.get("content") or []
        text = " ".join(block.get("text", "") for block in blocks if block.get("type") == "text").strip()
        if not text:
            return {"ok": False, "error": "Reponse vide Anthropic", "provider": provider}
        return {"ok": True, "provider": provider, "analysis": text}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "provider": provider}
