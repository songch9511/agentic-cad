from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CAD_SCRIPTS = REPO_ROOT / "skills" / "cad" / "scripts"


def ensure_repo_context() -> None:
    os.chdir(REPO_ROOT)
    cad_scripts = str(CAD_SCRIPTS)
    if cad_scripts not in sys.path:
        sys.path.insert(0, cad_scripts)


ensure_repo_context()

from cadref.lookup import build_selector_index  # noqa: E402
from common.catalog import StepImportOptions, source_from_path  # noqa: E402
from common.render import part_glb_path, part_selector_manifest_path, relative_to_repo  # noqa: E402
from common.step_scene import load_step_scene, scene_export_shape  # noqa: E402
from common.validators import geometry_summary_from_manifest  # noqa: E402


@dataclass(frozen=True)
class CheckResult:
    check: str
    passed: bool
    weight: float
    score: float
    message: str
    actual: object | None = None
    expected: object | None = None


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _weight(check: dict[str, Any]) -> float:
    value = check.get("weight", 1.0)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{check.get('type', 'check')} weight must be numeric")
    if float(value) < 0:
        raise ValueError(f"{check.get('type', 'check')} weight must be non-negative")
    return float(value)


def _result(
    check: dict[str, Any],
    *,
    passed: bool,
    message: str,
    actual: object | None = None,
    expected: object | None = None,
    fraction: float | None = None,
) -> CheckResult:
    weight = _weight(check)
    normalized_fraction = 1.0 if passed else 0.0
    if fraction is not None:
        normalized_fraction = max(0.0, min(1.0, float(fraction)))
    return CheckResult(
        check=str(check.get("type") or "unknown"),
        passed=bool(passed),
        weight=weight,
        score=weight * normalized_fraction,
        message=message,
        actual=actual,
        expected=expected,
    )


def _missing_manifest_result(check: dict[str, Any], manifest_path: Path) -> CheckResult:
    return _result(
        check,
        passed=False,
        message=f"topology manifest is missing or invalid: {relative_to_repo(manifest_path)}",
    )


def _number_list(value: object, *, field_name: str, length: int = 3) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise ValueError(f"{field_name} must be a list of {length} numbers")
    numbers: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"{field_name} must be a list of {length} numbers")
        numbers.append(float(item))
    return numbers


def _tolerances(value: object, *, length: int = 3) -> list[float]:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return [float(value)] * length
    return _number_list(value, field_name="tolerance", length=length)


def _evaluate_vector_close(check: dict[str, Any], actual: object, *, label: str) -> CheckResult:
    expected = _number_list(check.get("expected"), field_name=f"{label}.expected")
    tolerance = _tolerances(check.get("tolerance", 1e-6), length=len(expected))
    actual_values = _number_list(actual, field_name=f"{label}.actual", length=len(expected))
    errors = [abs(actual_values[index] - expected[index]) for index in range(len(expected))]
    axis_passes = [errors[index] <= tolerance[index] for index in range(len(expected))]
    passed = all(axis_passes)
    fraction = sum(1 for item in axis_passes if item) / len(axis_passes)
    return _result(
        check,
        passed=passed,
        fraction=fraction,
        message=f"{label} {'passed' if passed else 'failed'}",
        actual={"value": actual_values, "errors": errors},
        expected={"value": expected, "tolerance": tolerance},
    )


def _compare_count(check: dict[str, Any], actual: int) -> tuple[bool, str, dict[str, Any]]:
    expected: dict[str, Any] = {}
    if "equals" in check:
        expected["equals"] = int(check["equals"])
        if actual != expected["equals"]:
            return False, f"expected {expected['equals']}, got {actual}", expected
    if "min" in check:
        expected["min"] = int(check["min"])
        if actual < expected["min"]:
            return False, f"expected >= {expected['min']}, got {actual}", expected
    if "max" in check:
        expected["max"] = int(check["max"])
        if actual > expected["max"]:
            return False, f"expected <= {expected['max']}, got {actual}", expected
    if not expected:
        raise ValueError(f"{check.get('type')} requires equals, min, or max")
    return True, "count passed", expected


def _selector_count(summary: dict[str, object], selector: str) -> int:
    key_by_selector = {
        "occurrence": "occurrenceCount",
        "shape": "shapeCount",
        "face": "faceCount",
        "edge": "edgeCount",
        "vertex": "vertexCount",
    }
    key = key_by_selector.get(selector)
    if key is None:
        raise ValueError(f"Unsupported selector_count selector: {selector}")
    return int(summary.get(key) or 0)


def _row_radius(row: dict[str, Any]) -> float | None:
    params = row.get("params")
    if not isinstance(params, dict):
        return None
    radius = params.get("radius")
    if isinstance(radius, bool) or not isinstance(radius, (int, float)):
        return None
    return float(radius)


def _row_matches_radius(row: dict[str, Any], check: dict[str, Any]) -> bool:
    if "radius" not in check:
        return True
    expected = float(check["radius"])
    tolerance = float(check.get("radius_tolerance", 1e-6))
    actual = _row_radius(row)
    return actual is not None and abs(actual - expected) <= tolerance


def _surface_count(check: dict[str, Any], manifest: dict[str, Any]) -> CheckResult:
    index = build_selector_index(manifest)
    surface_type = str(check.get("surface_type") or "").strip().lower()
    if not surface_type:
        raise ValueError("surface_count requires surface_type")
    rows = [
        row
        for row in index.faces
        if str(row.get("surfaceType") or "").strip().lower() == surface_type and _row_matches_radius(row, check)
    ]
    passed, message, expected = _compare_count(check, len(rows))
    if "radius" in check:
        expected["radius"] = float(check["radius"])
        expected["radius_tolerance"] = float(check.get("radius_tolerance", 1e-6))
    return _result(
        check,
        passed=passed,
        message=message,
        actual={"count": len(rows), "selectors": [row.get("id") for row in rows]},
        expected=expected,
    )


def _curve_count(check: dict[str, Any], manifest: dict[str, Any]) -> CheckResult:
    index = build_selector_index(manifest)
    curve_type = str(check.get("curve_type") or "").strip().lower()
    if not curve_type:
        raise ValueError("curve_count requires curve_type")
    rows = [
        row
        for row in index.edges
        if str(row.get("curveType") or "").strip().lower() == curve_type and _row_matches_radius(row, check)
    ]
    passed, message, expected = _compare_count(check, len(rows))
    return _result(
        check,
        passed=passed,
        message=message,
        actual={"count": len(rows), "selectors": [row.get("id") for row in rows]},
        expected=expected,
    )


def _total_volume(manifest: dict[str, Any]) -> float:
    index = build_selector_index(manifest)
    total = 0.0
    for row in index.shapes:
        volume = row.get("volume")
        if isinstance(volume, (int, float)) and not isinstance(volume, bool):
            total += float(volume)
    return total


def _volume_range(check: dict[str, Any], manifest: dict[str, Any]) -> CheckResult:
    actual = _total_volume(manifest)
    minimum = float(check["min"]) if "min" in check else None
    maximum = float(check["max"]) if "max" in check else None
    if minimum is None and maximum is None:
        raise ValueError("volume_range requires min or max")
    passed = True
    if minimum is not None and actual < minimum:
        passed = False
    if maximum is not None and actual > maximum:
        passed = False
    return _result(
        check,
        passed=passed,
        message="volume passed" if passed else "volume failed",
        actual=actual,
        expected={"min": minimum, "max": maximum},
    )


def _valid_shape(check: dict[str, Any], step_path: Path) -> CheckResult:
    try:
        from OCP.BRepCheck import BRepCheck_Analyzer

        scene = load_step_scene(step_path)
        shape = scene_export_shape(scene)
        analyzer = BRepCheck_Analyzer(shape)
        passed = bool(analyzer.IsValid())
    except Exception as exc:
        return _result(
            check,
            passed=False,
            message=f"shape validity check failed: {type(exc).__name__}: {exc}",
        )
    return _result(
        check,
        passed=passed,
        message="shape is valid" if passed else "shape is invalid",
    )


def evaluate_step(step_path: Path | str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    resolved_step_path = Path(step_path).resolve()
    topology_path = part_selector_manifest_path(resolved_step_path)
    glb_path = part_glb_path(resolved_step_path)
    manifest = _read_json(topology_path)
    summary = geometry_summary_from_manifest(manifest) if manifest is not None else {}

    results: list[CheckResult] = []
    for check in checks:
        check_type = str(check.get("type") or "").strip()
        if check_type == "step_exists":
            results.append(
                _result(
                    check,
                    passed=resolved_step_path.exists(),
                    message="STEP exists" if resolved_step_path.exists() else "STEP is missing",
                    actual=relative_to_repo(resolved_step_path),
                )
            )
        elif check_type == "topology_exists":
            results.append(
                _result(
                    check,
                    passed=manifest is not None,
                    message="topology exists" if manifest is not None else "topology is missing or invalid",
                    actual=relative_to_repo(topology_path),
                )
            )
        elif check_type == "glb_exists":
            results.append(
                _result(
                    check,
                    passed=glb_path.exists(),
                    message="GLB exists" if glb_path.exists() else "GLB is missing",
                    actual=relative_to_repo(glb_path),
                )
            )
        elif check_type == "valid_shape":
            results.append(_valid_shape(check, resolved_step_path))
        elif manifest is None:
            results.append(_missing_manifest_result(check, topology_path))
        elif check_type == "bbox_size":
            results.append(_evaluate_vector_close(check, summary.get("size"), label="bbox_size"))
        elif check_type == "bbox_center":
            results.append(_evaluate_vector_close(check, summary.get("center"), label="bbox_center"))
        elif check_type == "selector_count":
            selector = str(check.get("selector") or "").strip().lower()
            actual = _selector_count(summary, selector)
            passed, message, expected = _compare_count(check, actual)
            results.append(_result(check, passed=passed, message=message, actual=actual, expected=expected))
        elif check_type == "surface_count":
            results.append(_surface_count(check, manifest))
        elif check_type == "curve_count":
            results.append(_curve_count(check, manifest))
        elif check_type == "volume_range":
            results.append(_volume_range(check, manifest))
        else:
            raise ValueError(f"Unsupported check type: {check_type}")

    score = sum(item.score for item in results)
    max_score = sum(item.weight for item in results)
    passed = all(item.passed for item in results)
    return {
        "stepPath": relative_to_repo(resolved_step_path),
        "topologyPath": relative_to_repo(topology_path),
        "glbPath": relative_to_repo(glb_path),
        "passed": passed,
        "score": score,
        "maxScore": max_score,
        "scorePct": 100.0 if max_score == 0 else (100.0 * score / max_score),
        "summary": summary,
        "checks": [asdict(item) for item in results],
    }


def _task_checks(task_file: Path, task_id: str) -> tuple[Path, list[dict[str, Any]]]:
    payload = _read_json(task_file)
    if payload is None:
        raise ValueError(f"Invalid task file: {task_file}")
    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError(f"{task_file} must contain a tasks list")
    for task in tasks:
        if isinstance(task, dict) and task.get("id") == task_id:
            target = task.get("target")
            checks = task.get("checks")
            if not isinstance(target, str) or not isinstance(checks, list):
                raise ValueError(f"Task {task_id} must define target and checks")
            kind = str(task.get("kind") or "part")
            source = source_from_path(
                (REPO_ROOT / target).resolve(),
                step_kind=kind,
                step_options=StepImportOptions(),
            )
            if source is None or source.step_path is None:
                raise ValueError(f"Task {task_id} target has no STEP output: {target}")
            return source.step_path, checks
    raise ValueError(f"Task id not found: {task_id}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate generated CAD artifacts against JSON benchmark checks.")
    parser.add_argument("step", nargs="?", help="STEP file to evaluate.")
    parser.add_argument("--task-file", help="Benchmark task JSON file.")
    parser.add_argument("--task-id", help="Task id whose checks should be used.")
    parser.add_argument("--checks-json", help="Inline JSON array of checks.")
    parser.add_argument("--json-out", help="Write evaluation result JSON to this path.")
    args = parser.parse_args(argv)

    if args.task_file or args.task_id:
        if not args.task_file or not args.task_id:
            parser.error("--task-file and --task-id must be provided together")
        task_step, checks = _task_checks((REPO_ROOT / args.task_file).resolve(), args.task_id)
        step = Path(args.step).resolve() if args.step else task_step
    else:
        if not args.step:
            parser.error("step is required unless --task-file and --task-id are provided")
        step = Path(args.step).resolve()
        checks = json.loads(args.checks_json) if args.checks_json else [{"type": "step_exists"}]
        if not isinstance(checks, list):
            parser.error("--checks-json must be a JSON array")

    result = evaluate_step(step, checks)
    output = json.dumps(result, indent=2, sort_keys=True)
    print(output)
    if args.json_out:
        output_path = (REPO_ROOT / args.json_out).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
