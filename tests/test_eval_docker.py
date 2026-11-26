from pathlib import Path
from types import SimpleNamespace

import eval.run as runner
from kit import stack


def test_task_image_cache_tag_includes_platform(tmp_path: Path, monkeypatch) -> None:
    task = tmp_path / "example-task"
    (task / "environment").mkdir(parents=True)
    monkeypatch.setattr(runner.stack, "cache_root", lambda: tmp_path / "cache")
    built_tags: list[str] = []
    monkeypatch.setattr(
        runner,
        "_built",
        lambda task, env_dir, tag: built_tags.append(tag) or tag,
    )

    image = runner.task_image(task)

    assert image == built_tags[0]
    assert image.endswith(f"-{stack.PLATFORM.replace('/', '-')}")


def test_task_image_build_uses_runner_platform(tmp_path: Path, monkeypatch) -> None:
    task = tmp_path / "example-task"
    environment = task / "environment"
    environment.mkdir(parents=True)
    (task / "task.toml").write_text("[environment]\nbuild_timeout_sec = 1\n")
    calls: list[tuple[list[str], dict[str, str] | None]] = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs.get("env")))
        if command[:3] == ["docker", "image", "inspect"]:
            return SimpleNamespace(returncode=1)
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        runner.stack,
        "build_env",
        lambda: {"DOCKER_DEFAULT_PLATFORM": stack.PLATFORM},
    )

    assert runner._built(task, environment, "example:amd64") == "example:amd64"
    assert calls[1][1]["DOCKER_DEFAULT_PLATFORM"] == stack.PLATFORM
    assert calls[1][1]["DOCKER_BUILDKIT"] == "1"
