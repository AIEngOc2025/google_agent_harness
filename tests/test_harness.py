import asyncio
import base64
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import taskbridge
import serve
from eval.synthetic import CASES, ScriptedMessage, ScriptedModel, SyntheticSession
from harness import AgentError, run_agent, run_tool


def test_scripted_agent_uses_instruction_and_task_workspace(tmp_path: Path) -> None:
    case = CASES[0]
    (tmp_path / "input.json").write_text(json.dumps(case["input"]), encoding="utf-8")
    session = SyntheticSession(tmp_path, case["instruction"])
    class ObservedModel(ScriptedModel):
        async def create(self, **kwargs):
            if self.step == 0:
                assert kwargs["messages"][1]["content"] == case["instruction"]
                assert str(tmp_path.resolve()) in kwargs["messages"][0]["content"]
            return await super().create(**kwargs)

    model = ObservedModel(case)
    asyncio.run(run_agent(session, model, "scripted"))
    assert session.operations == [
        "read:input.json", "write:result.json", "read:result.json"
    ]
    assert json.loads((tmp_path / "result.json").read_text()) == {"value": 45}


def test_tool_errors_are_returned_to_agent() -> None:
    class BrokenSession:
        def time_left(self):
            return None

        async def read_file(self, path):
            raise taskbridge.TaskError("file not found")

    session = BrokenSession()
    assert "Tool error" in asyncio.run(run_tool(session, "read_file", '{"path":"x"}'))
    assert "Tool error" in asyncio.run(run_tool(session, "read_file", "not-json"))
    assert "Tool error" in asyncio.run(run_tool(session, "unknown", "{}"))


def test_empty_truncated_and_unexpected_responses_are_not_success(tmp_path: Path) -> None:
    session = SyntheticSession(tmp_path, "test")

    class Model:
        chat = SimpleNamespace()

        def __init__(self, content, finish_reason):
            self.chat = SimpleNamespace(completions=self)
            self.content = content
            self.finish_reason = finish_reason

        async def create(self, **kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(
                    message=ScriptedMessage(content=self.content),
                    finish_reason=self.finish_reason,
                )],
                usage=None,
            )

    for content, reason in [(None, "stop"), ("partial", "length"), ("no", "content_filter"), ("done", "tool_calls")]:
        with pytest.raises(AgentError):
            asyncio.run(run_agent(session, Model(content, reason), "scripted"))


def test_turn_limit_is_an_error(tmp_path: Path) -> None:
    case = CASES[0]
    (tmp_path / "input.json").write_text(json.dumps(case["input"]))
    with pytest.raises(AgentError, match="limit"):
        asyncio.run(run_agent(SyntheticSession(tmp_path, case["instruction"]), ScriptedModel(case), "scripted", max_turns=1))


def test_expired_deadline_is_an_error(tmp_path: Path) -> None:
    class ExpiredSession(SyntheticSession):
        def time_left(self):
            return 0

    with pytest.raises(AgentError, match="deadline"):
        asyncio.run(run_agent(ExpiredSession(tmp_path, "test"), ScriptedModel(CASES[0]), "scripted"))


def test_server_requires_model_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MODEL_NAME", raising=False)
    with pytest.raises(RuntimeError, match="MODEL_NAME"):
        asyncio.run(serve.solve(taskbridge.Session(None, {"instruction": "test"})))


def test_real_taskbridge_frames_connect_model_and_task() -> None:
    case = CASES[0]

    class FakeWebSocket:
        def __init__(self):
            self.frames = asyncio.Queue()
            self.frames.put_nowait(json.dumps({
                "type": "task", "instruction": case["instruction"], "workdir": "/task"
            }))
            self.files = {"input.json": json.dumps(case["input"]).encode()}
            self.sent = []

        async def recv(self):
            return await self.frames.get()

        def __aiter__(self):
            return self

        async def __anext__(self):
            return await self.recv()

        async def send(self, raw):
            frame = json.loads(raw)
            self.sent.append(frame)
            if frame["type"] == "read_file":
                data = self.files[frame["path"]]
                result = {"content_b64": base64.b64encode(data).decode(), "size": len(data)}
            elif frame["type"] == "write_file":
                data = base64.b64decode(frame["content_b64"])
                self.files[frame["path"]] = data
                result = {"size": len(data)}
            else:
                return
            await self.frames.put(json.dumps({"type": "result", "id": frame["id"], "ok": True, **result}))

    async def exercise():
        socket = FakeWebSocket()
        async def handler(session):
            assert session.instruction == case["instruction"]
            assert session.workdir == "/task"
            return await run_agent(session, ScriptedModel(case), "scripted")
        await taskbridge._session(socket, handler)
        assert [f["type"] for f in socket.sent] == ["read_file", "write_file", "read_file", "done"]
        assert json.loads(socket.files["result.json"]) == {"value": 45}
        assert socket.sent[-1]["final_message"] == "Synthetic script completed."

    asyncio.run(exercise())
