"""PLE WebSocket entry point."""

import os

import openai
import taskbridge

from harness import run_agent


async def solve(session: taskbridge.Session) -> str:
    model = os.environ.get("MODEL_NAME")
    if not model:
        raise RuntimeError("MODEL_NAME is required.")
    if not os.environ.get("OPENAI_BASE_URL") or not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("The evaluator's model endpoint and key are required.")
    async with openai.AsyncOpenAI(max_retries=2, timeout=1800) as client:
        return await run_agent(session, client, model)


if __name__ == "__main__":
    taskbridge.run(solve)
