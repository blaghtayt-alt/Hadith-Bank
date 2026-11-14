#!/usr/bin/env python3
"""Observe baseline/candidate browser search latency and network bytes.

Measurements use real Chromium. A timed-out search is recorded as partial, not
as a completed no-result search. This script never modifies source material or
requires publication. Fresh browser contexts measure cold journeys; repeat
searches in the same context measure warm application/browser caches.
"""
import argparse
import asyncio
import contextlib
import datetime as dt
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import threading
import time
from urllib.parse import urlsplit


QUERIES = [
    ("Bukhari 1", "reference"),
    ("actions depend on intentions", "wording"),
    ("anger", "topic"),
    ("controlling anger", "topic"),
]


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def save(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError):
            pass


@contextlib.contextmanager
def local_server(directory):
    server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(directory)))
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.1}, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:" + str(server.server_port) + "/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


class NetworkLedger:
    """Chrome's observed encoded bytes, with cache/pending/error distinctions."""
    def __init__(self):
        self.rows = {}
        self.sequence = 0

    async def bind(self, page):
        self.session = await page.context.new_cdp_session(page)
        await self.session.send("Network.enable")
        self.session.on("Network.requestWillBeSent", self.request)
        self.session.on("Network.responseReceived", self.response)
        self.session.on("Network.loadingFinished", self.finished)
        self.session.on("Network.loadingFailed", self.failed)
        self.session.on("Network.dataReceived", self.data)

    def request(self, event):
        self.sequence += 1
        self.rows[event["requestId"]] = {"sequence": self.sequence, "url": event["request"]["url"],
            "started_monotonic": time.perf_counter(), "status": "pending", "encoded_bytes": 0,
            "received_encoded_bytes": 0, "from_disk_cache": False, "from_service_worker": False}

    def response(self, event):
        row = self.rows.get(event["requestId"])
        if row is not None:
            value = event["response"]
            row.update(http_status=value["status"], mime_type=value.get("mimeType"),
                       from_disk_cache=value.get("fromDiskCache", False),
                       from_service_worker=value.get("fromServiceWorker", False))

    def finished(self, event):
        row = self.rows.get(event["requestId"])
        if row is not None:
            row.update(status="complete", encoded_bytes=event["encodedDataLength"],
                       finished_monotonic=time.perf_counter())

    def failed(self, event):
        row = self.rows.get(event["requestId"])
        if row is not None:
            row.update(status="cancelled" if event.get("canceled") else "failed",
                       error=event.get("errorText"), finished_monotonic=time.perf_counter())

    def data(self, event):
        row = self.rows.get(event["requestId"])
        if row is not None:
            row["received_encoded_bytes"] += event.get("encodedDataLength", 0)

    def summary(self, after=0):
        rows = [dict(row) for row in self.rows.values() if row["sequence"] > after]
        return {"request_count": len(rows),
                "completed_request_count": sum(row["status"] == "complete" for row in rows),
                "pending_request_count": sum(row["status"] == "pending" for row in rows),
                "failed_or_cancelled_count": sum(row["status"] in ("failed", "cancelled") for row in rows),
                "completed_encoded_data_bytes": sum(row["encoded_bytes"] for row in rows if row["status"] == "complete"),
                "pending_received_encoded_bytes": sum(row["received_encoded_bytes"] for row in rows if row["status"] == "pending"),
                "disk_cached_responses": sum(bool(row["from_disk_cache"]) for row in rows),
                "service_worker_responses": sum(bool(row["from_service_worker"]) for row in rows),
                "requests": rows}


async def ui_state(page):
    return await page.evaluate("""() => ({
      busy: document.getElementById('results')?.getAttribute('aria-busy'),
      result: document.getElementById('result-count')?.textContent || '',
      error: document.querySelector('#results .error')?.textContent || null,
      home_visible: !!document.getElementById('discovery-home') && !document.getElementById('discovery-home').hidden,
      visible_cards: document.querySelectorAll('#results > .record-card, #results > .compact-result').length,
      first_ids: [...document.querySelectorAll('#results > .record-card, #results > .compact-result')]
        .slice(0,5).map(node=>node.dataset.occurrenceId),
      snapshot: (()=>{try {const s=JSON.parse(document.getElementById('hadith-snapshot').textContent);
        return {site:s.site,record_count:s.record_count,records_sha256:s.records_sha256,data_delivery:s.data_delivery};}
        catch(e) {return null;}})()
    })""")


async def wait_ready(page, timeout_ms):
    try:
        await page.wait_for_function("""() => {
          const result=document.getElementById('results');
          const count=document.getElementById('result-count');
          return result && count && result.getAttribute('aria-busy')==='false'
            && !/Updating results|Preparing the collection|Opening the collection/.test(count.textContent);
        }""", timeout=timeout_ms)
        state = await ui_state(page)
        return ("error" if state["error"] else "complete"), state
    except Exception as error:
        if error.__class__.__name__ != "TimeoutError":
            raise
        return "partial_timeout", await ui_state(page)


async def search(page, ledger, query, journey, timeout_ms, warmth):
    await page.locator("#query").fill("")
    mode = page.locator('input[name="search-mode"][value="' + journey + '"]')
    if await mode.count():
        await mode.check()
    marker = ledger.sequence
    started = time.perf_counter()
    await page.locator("#query").fill(query)
    submit = page.locator("#run-search")
    if await submit.count():
        await submit.click()
    status, state = await wait_ready(page, timeout_ms)
    elapsed = (time.perf_counter() - started) * 1000
    return {"query": query, "journey": journey, "warmth": warmth,
            "status": status, "elapsed_ms": round(elapsed, 3), "ui": state,
            "network": ledger.summary(marker), "observed_utc": now()}


async def benchmark_target(browser, name, url, args, report):
    target = {"name": name, "url": url, "runs": []}
    report["targets"].append(target)
    for query, journey in QUERIES:
        context = await browser.new_context(viewport={"width": 1366, "height": 900},
                                            locale="en-US", accept_downloads=True)
        page = await context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)[:600]))
        ledger = NetworkLedger()
        await ledger.bind(page)
        run = {"query": query, "journey": journey, "context": "fresh_isolated_browser_context", "measurements": []}
        target["runs"].append(run)
        try:
            started = time.perf_counter()
            response = await page.goto(url, wait_until="domcontentloaded", timeout=args.timeout_ms)
            html = await response.body()
            run["html"] = {"url": response.url, "status": response.status, "bytes": len(html),
                           "sha256": hashlib.sha256(html).hexdigest()}
            embedded = re.search(rb'<script\b[^>]*\bid="hadith-snapshot"[^>]*>(.*?)</script\s*>', html, re.S)
            if embedded:
                snapshot = json.loads(embedded.group(1))
                run["snapshot_identity"] = {key: snapshot.get(key) for key in
                    ("site", "record_count", "records_sha256", "data_delivery", "discovery")}
            status, state = await wait_ready(page, args.timeout_ms)
            run["startup"] = {"status": status, "elapsed_ms": round((time.perf_counter()-started)*1000, 3),
                              "ui": state, "network": ledger.summary()}
            save(args.report, report)
            if status == "complete":
                cold = await search(page, ledger, query, journey, args.timeout_ms, "cold")
                cold["journey_elapsed_ms"] = round(run["startup"]["elapsed_ms"] + cold["elapsed_ms"], 3)
                cold["journey_completed_encoded_data_bytes"] = (run["startup"]["network"]["completed_encoded_data_bytes"]
                                                                 + cold["network"]["completed_encoded_data_bytes"])
                run["measurements"].append(cold)
                save(args.report, report)
                # A timeout is a partial cold cache, so do not call the next run warm.
                if cold["status"] == "complete":
                    run["measurements"].append(await search(page, ledger, query, journey, args.timeout_ms, "warm"))
            run["page_errors"] = errors
        except Exception as error:
            run["execution_error"] = type(error).__name__ + ": " + str(error)[:1200]
        finally:
            save(args.report, report)
            await context.close()
        print(json.dumps({"target": name, "query": query,
                          "states": [{"warmth": item["warmth"], "status": item["status"],
                                      "ms": item["elapsed_ms"], "bytes": item["network"]["completed_encoded_data_bytes"]}
                                     for item in run["measurements"]]}, ensure_ascii=False), flush=True)
    identities = {(run.get("html", {}).get("sha256"),
                   json.dumps(run.get("snapshot_identity"), sort_keys=True))
                  for run in target["runs"]}
    target["same_snapshot_for_all_queries"] = len(identities) == 1


async def run(args, report, candidate_url, baseline_url=None):
    from playwright.async_api import async_playwright
    async with async_playwright() as playwright:
        options = {"headless": True}
        if args.chromium_executable:
            options["executable_path"] = str(args.chromium_executable.resolve())
        browser = await playwright.chromium.launch(**options)
        report["browser"] = {"name": "Chromium", "version": browser.version,
                             "viewport": {"width": 1366, "height": 900}}
        try:
            if baseline_url:
                await benchmark_target(browser, "baseline", baseline_url, args, report)
            if candidate_url:
                await benchmark_target(browser, "candidate", candidate_url, args, report)
        finally:
            await browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-url")
    parser.add_argument("--baseline-site-root", type=Path)
    parser.add_argument("--candidate-url")
    parser.add_argument("--site-root", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--chromium-executable", type=Path)
    parser.add_argument("--timeout-ms", type=int, default=120000)
    args = parser.parse_args()
    if args.site_root and args.candidate_url:
        parser.error("Use either --site-root or --candidate-url")
    if args.baseline_site_root and args.baseline_url:
        parser.error("Use either --baseline-site-root or --baseline-url")
    if not (args.baseline_url or args.baseline_site_root or args.candidate_url or args.site_root):
        parser.error("Supply at least one target")
    if not 1000 <= args.timeout_ms <= 300000:
        parser.error("timeout-ms must be between 1000 and 300000")
    report = {"schema": "hadith-bank-browser-search-benchmark-v1", "started_utc": now(),
              "status": "running", "targets": [],
              "method": {"cold": "New isolated browser context per query; startup is reported separately and in journey totals.",
                         "warm": "Repeat search in the same context only after the cold search completed.",
                         "bytes": "CDP Network.loadingFinished encodedDataLength for completed requests; cache and incomplete requests recorded separately. This is measured browser transport, not uncompressed file size.",
                         "timing": "Monotonic host elapsed time from UI input/submission until aria-busy=false; includes debounce, transport, decoding, ranking and rendering.",
                         "partial": "A timeout is not proof of no matches and is never recorded as a completed result.",
                         "source_identity": "Per-query HTML SHA-256 and embedded source stream/build binding; snapshot changes are explicitly flagged."}}
    save(args.report, report)
    try:
        with contextlib.ExitStack() as stack:
            candidate_url = (stack.enter_context(local_server(args.site_root.resolve()))
                             if args.site_root else args.candidate_url)
            baseline_url = (stack.enter_context(local_server(args.baseline_site_root.resolve()))
                            if args.baseline_site_root else args.baseline_url)
            report['environment_comparison'] = (
                'Both snapshots served locally on the same browser host; source/build bindings remain separate.'
                if args.site_root and args.baseline_site_root else
                'Targets may have different transport environments; do not attribute all latency differences to code.')
            asyncio.run(run(args, report, candidate_url, baseline_url))
        report["status"] = "observed"
        if any(run.get("execution_error") for target in report["targets"] for run in target["runs"]):
            report["status"] = "observed_with_execution_errors"
    except Exception as error:
        report["status"] = "blocked"
        report["error"] = type(error).__name__ + ": " + str(error)[:1500]
    report["finished_utc"] = now()
    save(args.report, report)
    print(json.dumps({"status": report["status"], "report": str(args.report)}, ensure_ascii=False))
    return 1 if report["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
