import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_logged_task.py"


class LoggedTaskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.job = self.root / "job"

    def tearDown(self):
        self.temp.cleanup()

    def argv(self, code, timeout=None):
        args = [sys.executable, str(SCRIPT), "run", "--job-dir", str(self.job),
                "--cwd", str(self.root)]
        if timeout is not None:
            args += ["--timeout", str(timeout)]
        return args + ["--", sys.executable, "-c", code]

    def invoke(self, args):
        result = subprocess.run(args, capture_output=True, text=True,
                                encoding="utf-8", timeout=15)
        self.assertLessEqual(len(result.stdout.encode("utf-8")), 8193)
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def run_code(self, code, timeout=None):
        return self.invoke(self.argv(code, timeout))

    def status(self, tail=0):
        return self.invoke([sys.executable, str(SCRIPT), "status", "--job-dir",
                            str(self.job), "--tail-bytes", str(tail)])

    def test_megabyte_single_line_stays_in_disk_log(self):
        code, state = self.run_code("import sys; sys.stdout.buffer.write(b'A' * (2 * 1024 * 1024))")
        self.assertEqual(code, 0)
        self.assertEqual(state["status"], "succeeded")
        self.assertEqual(state["log_bytes"], 2 * 1024 * 1024)
        self.assertNotIn("tail", state)
        _, tail = self.status(1000000)
        self.assertEqual(tail["tail_bytes_read"], 4096)
        self.assertEqual(tail["tail"], "[encoded data omitted]")

    def test_failure_exit_and_logs_are_retained(self):
        command = "import sys; print('actual failure'); sys.exit(7)"
        code, state = self.run_code(command)
        self.assertEqual(code, 7)
        self.assertEqual(state["status"], "failed")
        self.assertEqual(state["exit_code"], 7)
        self.assertIn("actual failure", (self.job / "output.log").read_text())
        repeat_code, repeat = self.run_code(command)
        self.assertEqual(repeat_code, 7)
        self.assertTrue(repeat["reused"])

    def test_completed_repeat_does_not_repeat_side_effect(self):
        command = "from pathlib import Path; p=Path('count'); p.write_text(p.read_text()+'x' if p.exists() else 'x')"
        self.assertEqual(self.run_code(command)[0], 0)
        code, state = self.run_code(command)
        self.assertEqual(code, 0)
        self.assertTrue(state["reused"])
        self.assertEqual((self.root / "count").read_text(), "x")

    def test_changed_identity_is_rejected(self):
        self.assertEqual(self.run_code("print('first')")[0], 0)
        code, state = self.run_code("print('different')")
        self.assertEqual(code, 64)
        self.assertEqual(state["request_status"], "rejected")
        self.assertEqual((self.job / "output.log").read_text().strip(), "first")

    def test_running_duplicate_refuses_and_status_is_readable(self):
        command = "from pathlib import Path; import time; Path('ready').write_text('x'); time.sleep(1.0)"
        first = subprocess.Popen(self.argv(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 5
            while not (self.root / "ready").exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue((self.root / "ready").exists())
            _, running = self.status()
            self.assertEqual(running["status"], "running")
            code, refused = self.run_code(command)
            self.assertEqual(code, 75)
            self.assertEqual(refused["request_status"], "refused")
            output, error = first.communicate(timeout=10)
            self.assertEqual(first.returncode, 0)
            self.assertEqual(error, b"")
            self.assertEqual(json.loads(output)["status"], "succeeded")
        finally:
            if first.poll() is None:
                first.kill()
                first.communicate()

    def test_simultaneous_claim_runs_exactly_once(self):
        command = "from pathlib import Path; import time; p=Path('count'); p.write_text(p.read_text()+'x' if p.exists() else 'x'); time.sleep(0.3)"
        processes = [subprocess.Popen(self.argv(command), stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE) for _ in range(2)]
        outcomes = []
        try:
            for process in processes:
                output, error = process.communicate(timeout=10)
                self.assertEqual(error, b"")
                outcomes.append((process.returncode, json.loads(output)))
        finally:
            for process in processes:
                if process.poll() is None:
                    process.kill()
                    process.communicate()
        self.assertEqual((self.root / "count").read_text(), "x")
        self.assertEqual(sum(not state.get("reused", False) and state.get("status") == "succeeded"
                             for _, state in outcomes), 1)
        self.assertTrue(all(code in (0, 75) for code, _ in outcomes))

    def test_timeout_checkpoint_is_terminal_and_not_reexecuted(self):
        command = "import time; time.sleep(10)"
        code, state = self.run_code(command, timeout=0.1)
        self.assertEqual(code, 124)
        self.assertEqual(state["status"], "timed_out")
        self.assertIsNotNone(state["exit_code"])
        self.assertEqual(state["tree_termination"], "requested")
        repeated_code, repeated = self.run_code(command, timeout=0.1)
        self.assertEqual(repeated_code, 124)
        self.assertTrue(repeated["reused"])

    def test_existing_unknown_job_is_not_overwritten(self):
        self.job.mkdir()
        code, state = self.run_code("print('never')")
        self.assertEqual(code, 75)
        self.assertEqual(state["status"], "recovery_required")
        self.assertFalse((self.job / "output.log").exists())

    def test_malformed_checkpoint_is_recovery_required(self):
        self.job.mkdir()
        (self.job / "status.json").write_text('{"status":"succeeded","wrapper_exit_code":null}')
        code, state = self.run_code("print('never')")
        self.assertEqual(code, 75)
        self.assertEqual(state["status"], "recovery_required")
        self.assertFalse((self.job / "output.log").exists())

    def test_timeout_stops_child_tree_side_effect(self):
        descendant = "from pathlib import Path; import time; time.sleep(0.8); Path('late-side-effect').write_text('bad')"
        command = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c'," + repr(descendant) + "]); time.sleep(10)"
        code, state = self.run_code(command, timeout=0.2)
        self.assertEqual(code, 124)
        self.assertEqual(state["tree_termination"], "requested")
        time.sleep(0.9)
        self.assertFalse((self.root / "late-side-effect").exists())

    def test_stdin_is_closed(self):
        code, _ = self.run_code("import sys; print(repr(sys.stdin.read()))")
        self.assertEqual(code, 0)
        self.assertEqual((self.job / "output.log").read_text().strip(), "''")

    def test_optional_tail_scrubs_secrets_and_bounds_unicode(self):
        command = "import sys; sys.stdout.buffer.write(('password=hide_me\\nAuthorization: Bearer hidden\\n' + '\\u6f22\\x01' * 3000).encode('utf-8'))"
        self.assertEqual(self.run_code(command)[0], 0)
        _, state = self.status(4096)
        self.assertLessEqual(state["tail_bytes_read"], 4096)
        self.assertLessEqual(len(json.dumps(state, ensure_ascii=True, separators=(',', ':'))), 8192)
        # Check credential redaction separately so it is inside the requested tail.
        self.job = self.root / "secrets"
        self.run_code("print('password=hide_me\\nAuthorization: Bearer hidden\\nhttps://user:pass@example.com')")
        _, state = self.status(4096)
        self.assertNotIn("hide_me", state["tail"])
        self.assertNotIn("Bearer hidden", state["tail"])
        self.assertNotIn("user:pass", state["tail"])

    def test_missing_executable_saves_failure(self):
        args = [sys.executable, str(SCRIPT), "run", "--job-dir", str(self.job),
                "--cwd", str(self.root), "--", str(self.root / "no-such-program")]
        code, state = self.invoke(args)
        self.assertEqual(code, 127)
        self.assertEqual(state["status"], "failed")
        self.assertIsNone(state["exit_code"])

    def test_invalid_arguments_are_bounded_without_echo(self):
        secret = "password=do_not_echo_" + "A" * 20000
        for args in (["status", "--job-dir", str(self.job), secret],
                     ["run", "--job-dir", str(self.job), "--cwd", str(self.root), "--timeout", secret]):
            code, state = self.invoke([sys.executable, str(SCRIPT)] + args)
            self.assertEqual(code, 64)
            self.assertEqual(state["status"], "rejected")
            self.assertNotIn("do_not_echo", json.dumps(state))

    def test_unicode_metadata_and_one_character_tail_cannot_stall_output(self):
        code = "import runpy; emit=runpy.run_path(" + repr(str(SCRIPT)) + ")[\"emit\"]; emit({k:'\\U0001f600'*512 for k in ['job_id','job_dir','log_path','error','started_at','finished_at']}|{'tail':'x','status':'running'})"
        result, state = self.invoke([sys.executable, "-c", code])
        self.assertEqual(result, 0)
        self.assertTrue(state["summary_truncated"])


if __name__ == "__main__":
    unittest.main()
