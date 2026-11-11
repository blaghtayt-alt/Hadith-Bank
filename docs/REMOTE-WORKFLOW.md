# Reliable remote work

## What the repair addresses

Repeated import sessions ended at the conversation-length limit while transferring large encoded files. The inspected remote call history included a successful write with roughly 983,000 characters of arguments and a command producing more than 220,000 bytes of output. Those observations do not establish a Remote Desktop Commander outage. The device was online and bounded command execution succeeded during diagnosis.

The repair keeps data and full logs on disk, preserves the outcome of a command, and stops a repeated request from executing the same job twice. It does not raise ChatGPT's conversation limit or make a failed command successful.

## Choose the transport first

1. Identify the machine holding the verified source and the current destination commit.
2. Check Git read access separately from write authentication. A successful `git ls-remote` does not establish push access. Use a dry-run push to an intended branch when shell Git will be the write route.
3. Prefer authenticated Git on the data-owning machine. The GitHub connector is another direct repository route; a missing shell credential does not imply that connector writes are unavailable.
4. If a file must cross environments, use a direct binary transfer or programmatically pass tool output into the next tool. Do not display or manually reproduce the encoded payload. Do not copy authentication tokens to another environment.
5. Verify byte counts and SHA-256 before importing a transferred archive. Reuse completed parts and existing originals. Record the exact source commit and destination ref before advancing publication.

Use one manifest/checkpoint throughout a transfer. A compact checkpoint needs `source_commit`, `destination_ref`, `expected_destination_commit`, expected file hashes, verified files or parts, completed stages, and any active call ID or PID. Keep it in `.work/` or outside the checkout. Check actual remote state after an uncertain response; a lost acknowledgement is not evidence that a write failed.

## Run commands with saved output

From the repository root, assign a new job directory to each intended execution:

```console
python scripts/run_logged_task.py run --job-dir .work/jobs/software-tests-001 --cwd . --timeout 600 -- python -m unittest discover -s tests
```

The runner executes an argument list without a shell. Its full combined output goes directly to `output.log`. Standard input is closed so an unexpected input prompt cannot wait indefinitely. Atomic `status.json` records the running process and final result. Console output is compact JSON; the original command's exit code remains available.

Inspect the same job after a Remote Commander response ends or the conversation resumes:

```console
python scripts/run_logged_task.py status --job-dir .work/jobs/software-tests-001
```

Request a short diagnostic tail only when needed:

```console
python scripts/run_logged_task.py status --job-dir .work/jobs/software-tests-001 --tail-bytes 2048
```

The tail is bounded by bytes, including a single extremely long line. Basic token/encoded-data redaction is a convenience, not a guarantee that arbitrary command output is free of sensitive content. Keep credentials out of command arguments and retain logs locally.

A completed job with the same invocation returns its saved result when requested again. A job already claimed, running, or left in an uncertain state is not launched a second time. A different command cannot reuse that job directory. Inspect the saved state and the actual process before deciding to start a new job ID. The runner intentionally does not clear stale execution claims or automatically retry commands with side effects.

The timeout applies only to the runner's own child process tree. It does not terminate other Remote Commander sessions or change device configuration. If the runner or machine disappears before saving a final status, the saved state can remain running/starting; that state must be investigated rather than treated as success.

## Distinguish the two asynchronous identifiers

| Returned identifier | Correct continuation |
| --- | --- |
| Remote MCP `call_id` with pending/executing status | Call `get_tool_result` with that ID. Do not repeat the original mutation. |
| Terminal PID from `start_process` | Call `read_process_output` with that PID, or inspect the runner's saved job directory. |
| No reliable acknowledgement | Inspect destination files/hashes, the saved job, and remote call status before deciding whether a retry is necessary. |

Remote terminal calls may return after a short bounded wait while the command continues. Increasing a requested wait does not turn a background result into an error. Keep tool output short and poll only the required status. Reading a single line of Base64 or JSON can still produce megabytes; use a script that emits selected metadata instead.

## Publish once, rebuild where the repository lives

The existing `.github/workflows/reader-pages.yml` runs validation, rebuilds the reader/catalog/search outputs, and deploys from current main. Transfer canonical material, preserved source evidence and changed code; avoid transporting all generated mirrors as another copy of the same import.

Before publishing, fetch current main and preserve concurrent work. Use normal fast-forward Git pushes or a connector ref update with an expected head. If that expectation changes, inspect the new commit and integrate it before trying again. Never force away another import to resolve a transfer problem.

Watch the workflow result and confirm the final published commit. A saved extraction test log establishes the result for that saved candidate only. It does not prove that the integrated current-main build or browser checks passed.

## Browser verification

Keep browser launch errors separate from import, transport and source-validation failures. Capture the exact startup error once. Use a browser/runtime that is actually available; do not repeatedly restart a prohibited or nonfunctional runtime, alter sandbox/security controls, or mark a skipped UI check as passed. Check the relevant rendered page and search behavior after a successful launch.

The preserved Persian Targhib browser report failed during initialization: Chromium reported `socket() failed: Operation not permitted (1)` and exited before loading the page. This is evidence about that Linux execution environment, not the bank's UI. Reusing the same failed launch flags is not a validation step. A browser startup smoke test on another machine establishes that the replacement runtime starts; the actual bank still requires its own page/search checks.
