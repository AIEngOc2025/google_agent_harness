from pathlib import Path
from types import SimpleNamespace

import pytest

import eval.synthetic as synthetic


def test_three_synthetic_scenarios_validate_independent_outputs(tmp_path: Path) -> None:
    summary = synthetic.run_evaluation(tmp_path / "run")
    assert summary["mode"] == "scripted_model_not_a_ple_score"
    assert summary["total_tasks"] == 3
    assert summary["successful_tasks"] == 3
    assert all(row["passed"] and row["error"] is None for row in summary["tasks"])
    assert summary["token_usage"] is None
    assert (tmp_path / "run" / "summary.json").is_file()


def test_wrong_synthetic_deliverable_is_not_a_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wrong_case = {**synthetic.CASES[0], "scripted_value": 999}
    monkeypatch.setattr(synthetic, "CASES", (wrong_case,))
    summary = synthetic.run_evaluation(tmp_path / "run")
    assert summary["successful_tasks"] == 0
    assert summary["tasks"][0]["error"]


def test_evaluation_can_use_an_explicitly_injected_client(tmp_path: Path) -> None:
    summary = synthetic.run_evaluation(
        tmp_path / "run",
        client_factory=synthetic.ScriptedModel,
        model_name="test-double",
        cases=(synthetic.CASES[0],),
    )
    assert summary["mode"] == "injected_model_not_a_ple_score"
    assert summary["successful_tasks"] == 1
    with pytest.raises(ValueError, match="explicitly"):
        synthetic.run_evaluation(tmp_path / "other", client_factory=synthetic.ScriptedModel)


def test_missing_deliverable_is_not_a_success(tmp_path: Path) -> None:
    class EarlyFinish(synthetic.ScriptedModel):
        async def create(self, **kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(
                    message=synthetic.ScriptedMessage(content="Finished."),
                    finish_reason="stop",
                )],
                usage=None,
            )

    summary = synthetic.run_evaluation(
        tmp_path / "run",
        client_factory=EarlyFinish,
        model_name="early-finish-double",
        cases=(synthetic.CASES[0],),
    )
    assert summary["successful_tasks"] == 0
    assert "FileNotFoundError" in summary["tasks"][0]["error"]


def test_synthetic_evaluation_refuses_artifacts_directory() -> None:
    with pytest.raises(ValueError, match="overlap"):
        synthetic.run_evaluation(Path("artifacts") / "synthetic-test")


def test_synthetic_evaluation_does_not_overwrite_existing_output(tmp_path: Path) -> None:
    output = tmp_path / "existing-run"
    output.mkdir()
    summary = output / "summary.json"
    summary.write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError, match="new or empty"):
        synthetic.run_evaluation(output)
    assert summary.read_text(encoding="utf-8") == "keep"
