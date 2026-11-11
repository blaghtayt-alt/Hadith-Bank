#!/usr/bin/env python3
"""Run one identified task with disk logs and bounded, resumable status output.

A job directory is an immutable execution claim. Never delete/reuse one to retry
an uncertain side effect: inspect the destination and use a new job directory.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import uuid

TERMINAL = {"succeeded", "failed", "timed_out", "interrupted"}
MAX_TAIL = 4096
MAX_SUMMARY = 8192


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def scrub(value):
    value = str(value)
    value = re.sub(r"https?://[^\s/@]+:[^\s/@]+@", "https://[redacted]@", value)
    value = re.sub(r"\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|xox[baprs]-[\w-]+)\b", "[redacted]", value)
    value = re.sub(r"(?i)\b(authorization\s*:\s*(?:bearer|basic))\s+\S+", r"\1 [redacted]", value)
    value = re.sub(r'''(?i)\b(password|passwd|token|secret|api[_-]?key)(\s*[:=]\s*)(?:"[^"]*"|'[^']*'|[^\s,;]+)''', r"\1\2[redacted]", value)
    return re.sub(r"[A-Za-z0-9+/_=-]{160,}", "[encoded data omitted]", value)


def emit(summary):
    # ASCII JSON also works in Windows consoles with a non-UTF-8 code page.
    encoded = json.dumps(summary, ensure_ascii=True, separators=(",", ":"))
    while len(encoded) > MAX_SUMMARY and summary.get("tail"):
        if len(summary["tail"]) <= 1:
            summary.pop("tail")
        else:
            summary["tail"] = summary["tail"][len(summary["tail"]) // 2:]
        summary["summary_truncated"] = True
        encoded = json.dumps(summary, ensure_ascii=True, separators=(",", ":"))
    if len(encoded) > MAX_SUMMARY:
        summary = {"status": scrub(summary.get("status", "recovery_required"))[:32],
                   "job_id": scrub(summary.get("job_id", ""))[:64],
                   "job_dir": scrub(summary.get("job_dir", ""))[:160],
                   "log_path": scrub(summary.get("log_path", ""))[:160],
                   "summary_truncated": True,
                   "message": "Status metadata exceeded the console limit; inspect the local status.json with a bounded read."}
        encoded = json.dumps(summary, ensure_ascii=True, separators=(",", ":"))
    if len(encoded) > MAX_SUMMARY:
        encoded = '{"status":"recovery_required","error":"Status metadata exceeded the console limit."}'
    print(encoded, flush=True)


def save_state(job_dir, state):
    temporary = job_dir / ("status." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(state, handle, ensure_ascii=True, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, job_dir / "status.json")
    finally:
        temporary.unlink(missing_ok=True)


def load_state(job_dir):
    try:
        with (job_dir / "status.json").open("rb") as handle:
            raw = handle.read(65537)
        if len(raw) > 65536:
            return None
        state = json.loads(raw)
        if not isinstance(state, dict) or state.get("schema_version") != 1:
            return None
        if not isinstance(state.get("command_sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", state["command_sha256"]):
            return None
        for key in ("job_id", "status", "started_at", "finished_at", "error", "tree_termination"):
            if state.get(key) is not None and not isinstance(state[key], str):
                return None
        for key in ("runner_pid", "child_pid", "exit_code", "wrapper_exit_code"):
            if state.get(key) is not None and type(state[key]) is not int:
                return None
        if state.get("status") in TERMINAL and type(state.get("wrapper_exit_code")) is not int:
            return None
        return state
    except (OSError, ValueError):
        return None


def summary_for(job_dir, state, tail_bytes=0, **extra):
    keys = ("job_id", "status", "runner_pid", "child_pid", "started_at",
            "finished_at", "exit_code", "wrapper_exit_code", "command_sha256",
            "tree_termination", "error")
    summary = {key: state[key] for key in keys if key in state}
    summary = {key: scrub(value)[:512] if isinstance(value, str) else value
               for key, value in summary.items()}
    summary["job_dir"] = scrub(job_dir)[:384]
    log = job_dir / "output.log"
    summary["log_path"] = scrub(log)[:384]
    try:
        summary["log_bytes"] = log.stat().st_size
        if tail_bytes:
            amount = min(max(0, tail_bytes), MAX_TAIL)
            with log.open("rb") as handle:
                handle.seek(max(0, summary["log_bytes"] - amount))
                raw = handle.read(amount)
            summary["tail_bytes_read"] = len(raw)
            summary["tail"] = scrub(raw.decode("utf-8", errors="replace"))
    except OSError:
        summary["log_bytes"] = None
    summary.update(extra)
    return summary


def stop_owned_tree(process, log):
    """Terminate only this runner's child tree, retaining the actual exit code."""
    if os.name == "nt":
        taskkill = str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "taskkill.exe")
        result = subprocess.run([taskkill, "/PID", str(process.pid), "/T", "/F"],
                                stdin=subprocess.DEVNULL, stdout=log,
                                stderr=subprocess.STDOUT, timeout=10, check=False)
        process.wait(timeout=5)
        return "requested" if result.returncode == 0 else "unconfirmed"
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass
    # The group can still contain grandchildren after its leader exits.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=5)
    return "requested"


def run_task(args):
    job_dir = Path(args.job_dir).expanduser().resolve()
    cwd = Path(args.cwd).expanduser().resolve()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or not cwd.is_dir():
        emit({"status": "rejected", "error": "A command and an existing working directory are required."})
        return 64
    identity = {"command": command, "cwd": str(cwd), "timeout": args.timeout}
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
    job_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        job_dir.mkdir()
    except FileExistsError:
        state = load_state(job_dir)
        if not state:
            emit({"status": "recovery_required", "job_dir": scrub(job_dir)[:384],
                  "error": "Job directory already claimed; its status is absent or unreadable. Inspect before retrying."})
            return 75
        if state.get("command_sha256") != fingerprint:
            emit(summary_for(job_dir, state, request_status="rejected",
                             error="This job directory belongs to a different command, directory or timeout."))
            return 64
        if state.get("status") in TERMINAL:
            emit(summary_for(job_dir, state, reused=True))
            return int(state.get("wrapper_exit_code", 74))
        emit(summary_for(job_dir, state, request_status="refused", reused=False,
                         error="Task is running or its outcome is uncertain. Read status; do not start it again."))
        return 75

    state = {"schema_version": 1, "job_id": uuid.uuid4().hex,
             "status": "starting", "runner_pid": os.getpid(), "child_pid": None,
             "started_at": now(), "finished_at": None, "exit_code": None,
             "wrapper_exit_code": None, "command_sha256": fingerprint}
    save_state(job_dir, state)
    process = None
    with (job_dir / "output.log").open("xb") as log:
        try:
            options = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
                       if os.name == "nt" else {"start_new_session": True})
            process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL,
                                       stdout=log, stderr=subprocess.STDOUT,
                                       shell=False, **options)
            state.update(status="running", child_pid=process.pid)
            save_state(job_dir, state)
            code = process.wait(timeout=args.timeout)
            state.update(status="succeeded" if code == 0 else "failed",
                         exit_code=code, wrapper_exit_code=code if code >= 0 else 128 - code)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            state.update(status="timed_out" if isinstance(error, subprocess.TimeoutExpired) else "interrupted",
                         wrapper_exit_code=124 if isinstance(error, subprocess.TimeoutExpired) else 130)
            if process is not None:
                try:
                    state["tree_termination"] = stop_owned_tree(process, log)
                except (OSError, subprocess.SubprocessError) as stop_error:
                    state["tree_termination"] = "unconfirmed"
                    state["error"] = scrub(stop_error)[:512]
                state["exit_code"] = process.poll()
                if state["exit_code"] is None:
                    state.update(status="recovery_required", wrapper_exit_code=75)
        except OSError as error:
            state.update(status="failed" if process is None else "recovery_required",
                         wrapper_exit_code=127 if process is None else 74,
                         error=scrub(error)[:512])
            if process is not None and process.poll() is None:
                try:
                    state["tree_termination"] = stop_owned_tree(process, log)
                except (OSError, subprocess.SubprocessError):
                    state["tree_termination"] = "unconfirmed"
            state["exit_code"] = process.poll() if process else None
        state["finished_at"] = now() if state["status"] in TERMINAL else None
        log.flush()
        save_state(job_dir, state)
    emit(summary_for(job_dir, state, reused=False))
    return state["wrapper_exit_code"]


def positive_timeout(value):
    number = float(value)
    if number <= 0 or not number < float("inf"):
        raise argparse.ArgumentTypeError("timeout must be a finite positive number")
    return number


class UsageError(Exception):
    pass


class BoundedParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse normally echoes the entire invalid value, which may itself be
        # a megabyte payload or a credential. Do not echo untrusted arguments.
        raise UsageError("Invalid command-line arguments. Use --help for the accepted options.")


def main(argv=None):
    parser = BoundedParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    run = commands.add_parser("run", help="claim and run one task; existing jobs are never relaunched")
    run.add_argument("--job-dir", required=True)
    run.add_argument("--cwd", required=True)
    run.add_argument("--timeout", type=positive_timeout)
    run.add_argument("command", nargs=argparse.REMAINDER)
    status = commands.add_parser("status", help="read the last checkpoint without starting anything")
    status.add_argument("--job-dir", required=True)
    status.add_argument("--tail-bytes", type=int, default=0)
    try:
        args = parser.parse_args(argv)
    except UsageError as error:
        emit({"status": "rejected", "error": str(error)})
        return 64
    try:
        if args.operation == "run":
            return run_task(args)
        job_dir = Path(args.job_dir).expanduser().resolve()
        state = load_state(job_dir)
        if not state:
            emit({"status": "recovery_required", "job_dir": scrub(job_dir)[:384],
                  "error": "No readable checkpoint. No command was started."})
            return 75
        emit(summary_for(job_dir, state, tail_bytes=args.tail_bytes))
        return 0
    except OSError as error:
        emit({"status": "recovery_required", "error": scrub(error)[:512],
              "message": "Inspect the job directory and destination before another execution."})
        return 74


if __name__ == "__main__":
    sys.exit(main())
