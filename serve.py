import os
import sys
import asyncio
from pathlib import Path
from openai import AsyncOpenAI

import taskbridge
from harness import run_agent

# Lecture des variables d'environnement officielles du serveur PLE (et fallback OpenAI)
MODEL_NAME = os.environ.get("MODEL_NAME") or os.environ.get("MODEL") or "google-cloud/gemini-3.8-flash"
MODEL_BASE_URL = os.environ.get("MODEL_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or "http://host.docker.internal:8001/v1"
MODEL_API_KEY = os.environ.get("MODEL_API_KEY") or os.environ.get("OPENAI_API_KEY") or "sk-placeholder"

client = AsyncOpenAI(
    base_url=MODEL_BASE_URL,
    api_key=MODEL_API_KEY,
)


async def solve(session: taskbridge.Session) -> str:
    """Point d'entrée appelé par taskbridge pour résoudre chaque tâche PLE."""
    model = os.environ.get("MODEL_NAME") or MODEL_NAME
    if not model:
        raise RuntimeError("MODEL_NAME environment variable is required.")

    base_url = os.environ.get("MODEL_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or MODEL_BASE_URL
    api_key = os.environ.get("MODEL_API_KEY") or os.environ.get("OPENAI_API_KEY") or MODEL_API_KEY

    active_client = AsyncOpenAI(base_url=base_url, api_key=api_key)
    max_turns = int(os.environ.get("MAX_TURNS", "120"))
    return await run_agent(session, active_client, model, max_turns=max_turns)


def main() -> None:
    socket_path = os.environ.get("TASKBRIDGE_SOCKET")
    ws_url = os.environ.get("TASKBRIDGE_URL") or os.environ.get("WS_URL")
    if socket_path:
        asyncio.run(taskbridge.serve_unix(socket_path, solve))
    elif ws_url:
        asyncio.run(taskbridge.serve_ws(ws_url, solve))
    else:
        host = os.environ.get("HOST", "0.0.0.0")
        port = int(os.environ.get("PORT", "8080"))
        asyncio.run(taskbridge.serve_tcp(host, port, solve))


if __name__ == "__main__":
    main()
