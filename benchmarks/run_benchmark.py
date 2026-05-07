from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from evaluator import REPO_ROOT, ensure_repo_context, evaluate_step


ensure_repo_context()

from common.catalog import StepImportOptions, source_from_path  # noqa: E402
from common.render import relative_to_repo  # noqa: E402


def _read_task_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid benchmark task file: {path}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("tasks"), list):
        raise ValueError(f"{path} must contain a JSON object with a tasks list")
    return payload


def _selected_tasks(payload: dict[str, Any], task_ids: list[str]) -> list[dict[str, Any]]:
    tasks = [task for task in payload["tasks"] if isinstance(task, dict)]
    if not task_ids:
        return tasks
    wanted = set(task_ids)
    selected = [task for task in tasks if str(task.get("id")) in wanted]
    missing = sorted(wanted - {str(task.get("id")) for task in selected})
    if missing:
        raise ValueError(f"Task id(s) not found: {', '.join(missing)}")
    return selected


def _source_for_task(task: dict[str, Any]) -> Any:
    target = task.get("target")
    if not isinstance(target, str) or not target.strip():
        raise ValueError(f"Task {task.get('id')} must define target")
    target_path = (REPO_ROOT / target).resolve()
    kind = str(task.get("kind") or "part")
    source = source_from_path(target_path, step_kind=kind, step_options=StepImportOptions())
    if source is None:
        raise ValueError(f"Task {task.get('id')} target is not a supported CAD source: {target}")
    if source.step_path is None:
        raise ValueError(f"Task {task.get('id')} target has no STEP output: {target}")
    return source


def _generator_command(source: Any, kind: str) -> list[str]:
    script_name = "gen_step_assembly" if kind == "assembly" else "gen_step_part"
    script = REPO_ROOT / "skills" / "cad" / "scripts" / script_name
    return [sys.executable, str(script), str(source.source_path), "--summary"]


def _run_generation(task: dict[str, Any], source: Any, *, timeout: float) -> dict[str, Any]:
    kind = str(task.get("kind") or source.kind or "part")
    started = time.perf_counter()
    command = _generator_command(source, kind)
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    elapsed = time.perf_counter() - started
    return {
        "command": command,
        "returnCode": completed.returncode,
        "elapsedSec": elapsed,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "passed": completed.returncode == 0,
    }


def run_benchmark(
    task_file: Path,
    *,
    task_ids: list[str],
    skip_generate: bool,
    timeout: float,
) -> dict[str, Any]:
    payload = _read_task_file(task_file)
    tasks = _selected_tasks(payload, task_ids)
    results: list[dict[str, Any]] = []

    for task in tasks:
        task_id = str(task.get("id") or "")
        source = _source_for_task(task)
        generation = {
            "passed": True,
            "skipped": True,
            "command": [],
            "returnCode": 0,
            "elapsedSec": 0.0,
            "stdout": "",
            "stderr": "",
        }
        if not skip_generate:
            generation = _run_generation(task, source, timeout=timeout)

        if generation["passed"]:
            evaluation = evaluate_step(source.step_path, task.get("checks") or [])
        else:
            evaluation = {
                "passed": False,
                "score": 0.0,
                "maxScore": sum(float(check.get("weight", 1.0)) for check in task.get("checks") or []),
                "scorePct": 0.0,
                "checks": [],
                "summary": {},
                "stepPath": relative_to_repo(source.step_path),
            }

        results.append(
            {
                "id": task_id,
                "prompt": task.get("prompt"),
                "target": relative_to_repo(source.source_path),
                "stepPath": relative_to_repo(source.step_path),
                "generation": generation,
                "evaluation": evaluation,
                "passed": bool(generation["passed"] and evaluation["passed"]),
                "scorePct": evaluation["scorePct"],
            }
        )

    passed_count = sum(1 for result in results if result["passed"])
    average_score = 0.0 if not results else sum(float(result["scorePct"]) for result in results) / len(results)
    return {
        "schemaVersion": 1,
        "taskFile": relative_to_repo(task_file),
        "taskCount": len(results),
        "passedCount": passed_count,
        "failedCount": len(results) - passed_count,
        "averageScorePct": average_score,
        "results": results,
    }


def _print_summary(result: dict[str, Any]) -> None:
    print(
        f"Benchmark: {result['passedCount']}/{result['taskCount']} passed, "
        f"average={result['averageScorePct']:.1f}%"
    )
    for row in result["results"]:
        status = "PASS" if row["passed"] else "FAIL"
        print(f"{status} {row['id']}: {row['scorePct']:.1f}% {row['stepPath']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Agentic CAD benchmark tasks.")
    parser.add_argument("task_file", help="JSON benchmark task file.")
    parser.add_argument("--task-id", action="append", default=[], help="Run only this task id. Repeatable.")
    parser.add_argument("--skip-generate", action="store_true", help="Evaluate existing STEP/topology artifacts.")
    parser.add_argument("--timeout", type=float, default=180.0, help="Per-task generation timeout in seconds.")
    parser.add_argument("--json-out", help="Write benchmark result JSON to this path.")
    args = parser.parse_args(argv)

    result = run_benchmark(
        (REPO_ROOT / args.task_file).resolve(),
        task_ids=args.task_id,
        skip_generate=args.skip_generate,
        timeout=args.timeout,
    )
    _print_summary(result)
    if args.json_out:
        output_path = (REPO_ROOT / args.json_out).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Wrote JSON: {relative_to_repo(output_path)}")
    return 0 if result["failedCount"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
