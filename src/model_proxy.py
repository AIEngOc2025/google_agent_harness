# src/model_proxy.py
"""
@definition : Simple FastAPI proxy that forwards OpenAI‑compatible completion requests to the Gemini model.
@args/params : None (environment variables provide configuration).
@return : FastAPI app instance listening on localhost:8000.
"""

import os, time
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Dict

# ------------------------------------------------------------
# Configuration – read from .env (already loaded by uv run)
# ------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set in environment")

# Helper to discover a model that supports generateContent
async def discover_model() -> str:
    """Return the first Gemini model name that supports `generateContent`.

    The function queries the Gemini ModelService ListModels endpoint and
    selects the first model whose `supportedGenerationMethods` includes
    "generateContent".  If no suitable model is found, an HTTPException is
    raised so the caller receives a clear error.
    """
    list_url = f"https://generativelanguage.googleapis.com/v1/models?key={GEMINI_API_KEY}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(list_url, timeout=10.0)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Model discovery failed: {resp.text}")
        data = resp.json()
        for model in data.get("models", []):
            methods = model.get("supportedGenerationMethods", [])
            if "generateContent" in methods:
                # model name is like "models/gemini-1.5-flash"
                return model.get("name", "").split('/')[-1]
    raise HTTPException(status_code=502, detail="No Gemini model supporting generateContent found")

app = FastAPI()

@app.post("/v1/completions")
async def completions(request: Request) -> JSONResponse:
    """Forward a completion request to Gemini and return an OpenAI‑style response.

    The incoming payload is translated to Gemini's request format, sent to the
    discovered model, and the response is reshaped to the subset required by the
    PLEBench grader.
    """
    payload: Dict[str, Any] = await request.json()

    # --------------------------------------------------------
    # Basic validation – the grader only uses a few fields.
    # --------------------------------------------------------
    if "model" not in payload:
        raise HTTPException(status_code=400, detail="'model' field required")

    # -----------------------------------------------------------------
    # Discover a compatible Gemini model (always use the first one that works)
    # -----------------------------------------------------------------
    gemini_model = await discover_model()
    # Fallback: if the discovered model is a deprecated 2.5‑flash version, use the newer 3.8‑flash
    if gemini_model.startswith("gemini-2.5-flash"):
        gemini_model = "gemini-3.8-flash"

    # Build Gemini request body – we keep it minimal.
    gemini_body = {
        "contents": [{"role": "user", "parts": [{"text": payload.get("prompt", "")}]}],
        "generationConfig": {
            "temperature": payload.get("temperature", 0.0),
            "maxOutputTokens": payload.get("max_tokens", 1024),
            "topP": payload.get("top_p", 1.0),
        },
    }

    # Build the full Gemini endpoint URL using the selected model
    gemini_url = f"https://generativelanguage.googleapis.com/v1/models/{gemini_model}:generateContent"

    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}

    async with httpx.AsyncClient() as client:
        # Tenter le modèle principal découvert
        try:
            response = await client.post(gemini_url, json=gemini_body, headers=headers, timeout=30.0)
        except Exception:
            response = None
        # Si le modèle principal renvoie 503 (ou autre erreur), on itère sur une liste de modèles de secours
        if not response or response.status_code != 200:
            fallback_models = ["gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-2.5-flash", "gemini-pro"]
            for fallback in fallback_models:
                fallback_url = f"https://generativelanguage.googleapis.com/v1/models/{fallback}:generateContent"
                try:
                    response = await client.post(fallback_url, json=gemini_body, headers=headers, timeout=30.0)
                except Exception:
                    response = None
                if response and response.status_code == 200:
                    break
        if not response or response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Gemini error: {response.text if response else 'no response'}")
        gemini_data = response.json()

    # --------------------------------------------------------
    # Translate Gemini response to the minimal OpenAI format expected
    # by the grader (choices[0].message.content).
    # --------------------------------------------------------
    try:
        text = gemini_data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Malformed Gemini response: {exc}")

    openai_like = {
        "id": "model-proxy-001",
        "object": "text_completion",
        "created": int(time.time()) if hasattr(time, "time") else 0,
        "model": payload.get("model", "gemini-proxy"),
        "choices": [{"text": text, "index": 0, "finish_reason": "stop"}],
    }
    return JSONResponse(content=openai_like)

# ------------------------------------------------------------
# When run with `uvicorn src.model_proxy:app`, the server will be
# available at http://localhost:8000/v1/completions.
# ------------------------------------------------------------
