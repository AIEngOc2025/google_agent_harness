import csv
import io
import json
from pathlib import Path
from typing import Any

import pytest

from eval.metrics import analyze
from eval.run import select_tasks
from eval.splits import task_ids
from kit.artifacts import load_dev_set, DEV_SET_FILE


def _write_run(
    run_dir: Path,
    *,
    name: str,
    scores: dict[str, float],
    input_tokens: int,
    output_tokens: int,
) -> Path:
    tasks: list[dict[str, Any]] = []
    for task_id, score in scores.items():
        trial = Path("attempt1") / "jobs" / task_id
        trajectory_dir = run_dir / trial / "agent"
        trajectory_dir.mkdir(parents=True)
        (trajectory_dir / "trajectory.json").write_text(
            json.dumps(
                {
                    "steps": [
                        {
                            "source": "agent",
                            "metrics": {
                                "n_prompt_tokens": 10,
                                "n_completion_tokens": 2,
                            },
                            "tool_calls": [
                                {
                                    "function": {
                                        "name": "read_file",
                                        "arguments": "private",
                                    }
                                }
                            ],
                        },
                        {
                            "source": "agent",
                            "metrics": {"n_input_tokens": 5, "n_output_tokens": 1},
                            "finish_reason": "stop",
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        tasks.append(
            {
                "id": task_id,
                "score": score,
                "measured": True,
                "kind": "ok",
                "status": "ok",
                "tokens": {"input": input_tokens, "output": output_tokens},
                "trial": str(trial),
            }
        )
    run_dir.mkdir(parents=True, exist_ok=True)
    results = run_dir / "results.json"
    results.write_text(
        json.dumps(
            {
                "submission": name,
                "model": "google-cloud/model-flash",
                "evaluation_split": "holdout",
                "score": sum(scores.values()) / len(scores),
                "complete": True,
                "tasks": tasks,
            }
        ),
        encoding="utf-8",
    )
    return results


def test_fixed_split_reserves_nine_tasks_by_default() -> None:
    dev = load_dev_set(DEV_SET_FILE)
    development = task_ids(dev, "dev")
    holdout = task_ids(dev, "holdout")

    assert len(development) == 20
    assert len(holdout) == 9
    assert set(development).isdisjoint(holdout)
    assert set(development) | set(holdout) == set(dev)
    assert task_ids(dev, "all") == list(dev)
    with pytest.raises(SystemExit, match="not selected evaluation tasks"):
        select_tasks("wind-diaphragm-shear", {task: dev[task] for task in development})


def test_metrics_compare_matching_baseline_and_extract_trace(
    tmp_path: Path,
) -> None:
    task_scores = {
        "data-center-site-model": 0.4,
        "lv-cable-sizing": 0.5,
    }
    baseline = _write_run(
        tmp_path / "baseline",
        name="react",
        scores=task_scores,
        input_tokens=100,
        output_tokens=20,
    )
    candidate = _write_run(
        tmp_path / "candidate",
        name="harness",
        scores={"data-center-site-model": 0.8, "lv-cable-sizing": 1.0},
        input_tokens=80,
        output_tokens=10,
    )

    report = analyze(
        [candidate],
        [baseline],
        tmp_path / "report",
        dev_set_path=DEV_SET_FILE,
        input_cost_per_million=2,
        output_cost_per_million=4,
    )

    candidate_rows = [row for row in report["runs"] if not row["is_baseline"]]
    assert candidate_rows[0]["mean_measured_score"] == pytest.approx(0.9)
    assert candidate_rows[0]["grader_return_rate"] == 1
    assert candidate_rows[0]["total_tokens"] == 180
    assert len(report["pareto_frontier"]) == 1
    by_task = {
        row["task_id"]: row
        for row in csv.DictReader(
            io.StringIO((tmp_path / "report" / "tasks.csv").read_text(encoding="utf-8"))
        )
        if row["run_id"] == "candidate"
    }
    assert float(by_task["lv-cable-sizing"]["score_delta"]) == pytest.approx(0.5)
    assert by_task["data-center-site-model"]["discipline"] == "Civil engineering"
    assert by_task["data-center-site-model"]["stop_reason"] == "stop"
    assert json.loads(by_task["data-center-site-model"]["tool_calls"]) == ["read_file"]
    assert float(by_task["data-center-site-model"]["estimated_cost"]) == pytest.approx(
        0.0002
    )
    assert "private" not in (tmp_path / "report" / "tasks.csv").read_text(
        encoding="utf-8"
    )
    assert (tmp_path / "report" / "score_vs_tokens.csv").is_file()
    traces = json.loads(
        (tmp_path / "report" / "traces.json").read_text(encoding="utf-8")
    )
    candidate_trace = next(row for row in traces if row["run_id"] == "candidate")
    assert candidate_trace["step_token_usage"] == [
        {"step": 0, "input": 10, "output": 2},
        {"step": 1, "input": 5, "output": 1},
    ]
    assert candidate_trace["stop_reason"] == "stop"
    assert "private" not in json.dumps(candidate_trace)


def test_failure_cause_labels_must_name_a_known_task(tmp_path: Path) -> None:
    result = _write_run(
        tmp_path / "run",
        name="candidate",
        scores={"data-center-site-model": 0.5},
        input_tokens=1,
        output_tokens=1,
    )
    labels = tmp_path / "labels.json"
    labels.write_text(
        json.dumps({"run": {"unknown-task": "parsing"}}), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="unknown tasks"):
        analyze(
            [result],
            [],
            tmp_path / "report",
            dev_set_path=DEV_SET_FILE,
            failure_labels_path=labels,
        )
