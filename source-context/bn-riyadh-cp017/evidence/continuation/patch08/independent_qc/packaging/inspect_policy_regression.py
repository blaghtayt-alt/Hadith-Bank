#!/usr/bin/env python3
"""Focused synthetic tests for the --inspect path-policy correction only."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

sys.dont_write_bytecode = True
RAW = Path(__file__).absolute().parents[2]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inspect_fixture(module, source, relative):
    """Mock only parent authentication; run the actual inspect command branch."""
    with tempfile.TemporaryDirectory(prefix="patch08_inspect_policy_") as temporary:
        workspace = Path(temporary)
        roots = {"parent": workspace / "parent" / module.PARENT_PREFIX,
                 "stage": workspace / "stage" / module.PREFIX,
                 "raw": workspace / "raw"}
        for root in roots.values():
            root.mkdir(parents=True)
        target = roots[source] / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"synthetic path policy fixture\n")
        before = sorted(p.relative_to(workspace).as_posix() for p in workspace.rglob("*"))
        events = []
        original_parent, original_progress, original_argv = module.Parent, module.progress, sys.argv
        module.Parent = lambda *args, **kwargs: SimpleNamespace(expected={})
        module.progress = lambda phase, **fields: events.append({"phase": phase, **fields})
        sys.argv = ["packager", "--inspect", "--workspace", str(workspace)]
        for name, root in roots.items():
            sys.argv.extend(["--" + name + "-root", str(root)])
        error = None
        try:
            module.main()
        except ValueError as exc:
            error = str(exc)
        finally:
            module.Parent, module.progress, sys.argv = original_parent, original_progress, original_argv
        after = sorted(p.relative_to(workspace).as_posix() for p in workspace.rglob("*"))
        assert after == before, "Inspect created, deleted or renamed a fixture input"
        assert target.read_bytes() == b"synthetic path policy fixture\n", "Inspect changed fixture bytes"
        return error, events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, help="Optional pre-fix source to reproduce the diagnostic defect")
    args = parser.parse_args()
    current_path = RAW / "package_patch08_streaming.py"
    module = load(current_path, "packaging_inspect_current")
    tests = []
    if args.before:
        before = load(args.before, "packaging_inspect_before")
        error, events = inspect_fixture(before, "raw", "unexpected.zip")
        assert error is None and events[-1]["new_nested_archives"] == 0
        tests.append({"test": "original_inspect_misreported_nested_archive_as_zero", "status": "reproduced",
                      "sha256": hashlib.sha256(args.before.read_bytes()).hexdigest()})
    cases = [("raw", "unexpected.zip", "New nested archive rejected"),
             ("stage", "unexpected.zip.001", "New nested archive rejected"),
             ("stage", "data/all_source_paragraphs.jsonl", "Immutable source/history"),
             ("stage", "originals/new_source.txt", "Immutable source/history")]
    for source, relative, expected in cases:
        error, events = inspect_fixture(module, source, relative)
        assert error is not None and expected in error, (source, relative, error, events)
        tests.append({"test": "inspect_rejects_" + source + ":" + relative, "status": "pass", "error": error})
    error, events = inspect_fixture(module, "raw", "independent_qc/synthetic.json")
    assert error is None and events[-1]["status"] == "pass"
    assert events[-1]["final_report_present"] is False
    assert events[-1]["input_bytes_frozen_or_release_packaged"] is False
    tests.append({"test": "ordinary_inspect_remains_read_only_without_final_report_or_freeze", "status": "pass"})
    with tempfile.TemporaryDirectory(prefix="patch08_inventory_policy_") as temporary:
        stage, raw = Path(temporary) / "stage", Path(temporary) / "raw"
        stage.mkdir(); raw.mkdir()
        (raw / "unexpected.zip").write_bytes(b"synthetic archive path")
        try:
            module.inventory_new(stage, raw)
        except ValueError as exc:
            assert "New nested archive rejected" in str(exc)
        else:
            raise AssertionError("Freeze inventory stopped rejecting nested archives")
    tests.append({"test": "freeze_inventory_still_rejects_nested_archive_with_shared_policy", "status": "pass"})
    print(json.dumps({"status": "pass", "scope": "Focused synthetic inspect input-path regression only",
        "reviewed_packager_sha256": hashlib.sha256(current_path.read_bytes()).hexdigest(),
        "mocked_parent_authentication": True, "real_release_freeze_or_export_performed": False,
        "tests": tests}, indent=2))


if __name__ == "__main__":
    main()
