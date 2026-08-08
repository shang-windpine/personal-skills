#!/usr/bin/env python3
"""Readonly Sumo Logic log search via Search Job API (stdlib only)."""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_CRED_PATH = Path.home() / ".config" / "sumologic" / "credentials"
DONE_STATES = {
    "DONE GATHERING RESULTS",
    "DONE GATHERING HISTOGRAM",
    "CANCELLED",
    "FORCE PAUSED",
}
FAILED_STATES = {"CANCELLED", "FORCE PAUSED"}


def die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def load_credentials(path: Path) -> dict[str, str]:
    creds: dict[str, str] = {}
    for key in ("SUMO_ACCESS_ID", "SUMO_ACCESS_KEY", "SUMO_API_ENDPOINT"):
        val = os.environ.get(key)
        if val:
            creds[key] = val.strip()

    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key in ("SUMO_ACCESS_ID", "SUMO_ACCESS_KEY", "SUMO_API_ENDPOINT") and value:
                creds.setdefault(key, value)

    missing = [k for k in ("SUMO_ACCESS_ID", "SUMO_ACCESS_KEY", "SUMO_API_ENDPOINT") if not creds.get(k)]
    if missing:
        die(
            "Missing credentials: "
            + ", ".join(missing)
            + f"\nSet them in {path} (chmod 600) or as environment variables."
        )

    endpoint = creds["SUMO_API_ENDPOINT"].rstrip("/")
    if endpoint.endswith("/api"):
        endpoint = endpoint[: -len("/api")]
    creds["SUMO_API_ENDPOINT"] = endpoint
    return creds


def parse_time(value: str, *, now: datetime | None = None) -> int:
    """Return epoch milliseconds. Accepts epoch ms/s, ISO-8601, or relative like -15m / -1h / -1d."""
    now = now or datetime.now(timezone.utc)
    value = value.strip()

    if value.lower() == "now":
        return int(now.timestamp() * 1000)

    if re.fullmatch(r"-?\d+", value):
        n = int(value)
        # Heuristic: 13+ digits => ms, otherwise seconds
        return n if abs(n) >= 10_000_000_000 else n * 1000

    rel = re.fullmatch(r"-(\d+)([smhd])", value, flags=re.IGNORECASE)
    if rel:
        amount = int(rel.group(1))
        unit = rel.group(2).lower()
        delta = {
            "s": timedelta(seconds=amount),
            "m": timedelta(minutes=amount),
            "h": timedelta(hours=amount),
            "d": timedelta(days=amount),
        }[unit]
        return int((now - delta).timestamp() * 1000)

    # ISO-8601; strip trailing Z
    iso = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError as exc:
        die(f"Invalid time value: {value!r} ({exc})")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


class SumoClient:
    def __init__(self, access_id: str, access_key: str, endpoint: str) -> None:
        self.base = f"{endpoint.rstrip('/')}/api/v1"
        self.cookie_jar = http.cookiejar.CookieJar()
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, self.base, access_id, access_key)
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar),
            urllib.request.HTTPBasicAuthHandler(password_mgr),
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base}{path}"
        if query:
            qs = urllib.parse.urlencode({k: str(v) for k, v in query.items()})
            url = f"{url}?{qs}"
        data = None
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener.open(req, timeout=60) as resp:
                raw = resp.read()
                if not raw:
                    return None
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            # Never echo credentials; response body is enough for debugging.
            die(f"HTTP {exc.code} {method} {path}: {detail}")
        except urllib.error.URLError as exc:
            die(f"Request failed: {exc.reason}")


def create_job(client: SumoClient, query: str, from_ms: int, to_ms: int, timezone_name: str) -> str:
    payload = {
        "query": query,
        "from": from_ms,
        "to": to_ms,
        "timeZone": timezone_name,
        "byReceiptTime": False,
    }
    result = client.request("POST", "/search/jobs", body=payload)
    if not isinstance(result, dict) or "id" not in result:
        die(f"Unexpected create job response: {result!r}")
    return str(result["id"])


def wait_for_job(client: SumoClient, job_id: str, timeout_s: int, poll_s: float) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    status: dict[str, Any] = {}
    while time.time() < deadline:
        status = client.request("GET", f"/search/jobs/{job_id}")
        state = status.get("state", "")
        if state in DONE_STATES:
            if state in FAILED_STATES:
                die(f"Search job ended with state={state}: {json.dumps(status)}")
            return status
        time.sleep(poll_s)
    die(f"Timed out after {timeout_s}s waiting for job {job_id}. Last status: {json.dumps(status)}")


def fetch_messages(client: SumoClient, job_id: str, limit: int) -> list[dict[str, Any]]:
    result = client.request(
        "GET",
        f"/search/jobs/{job_id}/messages",
        query={"offset": 0, "limit": limit},
    )
    messages = result.get("messages", []) if isinstance(result, dict) else []
    out: list[dict[str, Any]] = []
    for item in messages:
        # Sumo wraps each row as {"map": {...}}
        if isinstance(item, dict) and "map" in item and isinstance(item["map"], dict):
            out.append(item["map"])
        elif isinstance(item, dict):
            out.append(item)
    return out


def fetch_records(client: SumoClient, job_id: str, limit: int) -> list[dict[str, Any]]:
    result = client.request(
        "GET",
        f"/search/jobs/{job_id}/records",
        query={"offset": 0, "limit": limit},
    )
    records = result.get("records", []) if isinstance(result, dict) else []
    out: list[dict[str, Any]] = []
    for item in records:
        if isinstance(item, dict) and "map" in item and isinstance(item["map"], dict):
            out.append(item["map"])
        elif isinstance(item, dict):
            out.append(item)
    return out


def delete_job(client: SumoClient, job_id: str) -> None:
    try:
        client.request("DELETE", f"/search/jobs/{job_id}")
    except SystemExit:
        # Cleanup best-effort; do not hide prior success.
        pass


def compact_message(msg: dict[str, Any]) -> dict[str, Any]:
    keep = ("_messagetime", "_receipttime", "_sourcecategory", "_sourcehost", "_source", "_collector", "_raw")
    return {k: msg[k] for k in keep if k in msg}


def main() -> None:
    parser = argparse.ArgumentParser(description="Readonly Sumo Logic log search")
    parser.add_argument("--query", "-q", required=True, help="Sumo query string")
    parser.add_argument("--from", dest="from_time", default="-15m", help="Start time (default: -15m)")
    parser.add_argument("--to", dest="to_time", default="now", help="End time (default: now)")
    parser.add_argument("--limit", type=int, default=50, help="Max messages/records (default: 50)")
    parser.add_argument("--timezone", default="UTC", help="Query timezone (default: UTC)")
    parser.add_argument("--timeout", type=int, default=120, help="Seconds to wait for job completion")
    parser.add_argument("--credentials", type=Path, default=DEFAULT_CRED_PATH)
    parser.add_argument("--raw", action="store_true", help="Print full message maps without compaction")
    parser.add_argument("--keep-job", action="store_true", help="Do not delete the search job after fetch")
    args = parser.parse_args()

    if args.limit < 1 or args.limit > 1000:
        die("--limit must be between 1 and 1000")

    creds = load_credentials(args.credentials)
    from_ms = parse_time(args.from_time)
    to_ms = parse_time(args.to_time)
    if from_ms >= to_ms:
        die("--from must be earlier than --to")

    client = SumoClient(creds["SUMO_ACCESS_ID"], creds["SUMO_ACCESS_KEY"], creds["SUMO_API_ENDPOINT"])
    job_id = create_job(client, args.query, from_ms, to_ms, args.timezone)
    try:
        status = wait_for_job(client, job_id, args.timeout, poll_s=2.0)
        message_count = int(status.get("messageCount") or 0)
        record_count = int(status.get("recordCount") or 0)

        # Aggregation queries expose records; raw searches expose messages.
        if message_count > 0:
            rows = fetch_messages(client, job_id, args.limit)
            kind = "messages"
            if not args.raw:
                rows = [compact_message(r) for r in rows]
        elif record_count > 0:
            rows = fetch_records(client, job_id, args.limit)
            kind = "records"
        else:
            rows = []
            kind = "messages"

        out = {
            "jobId": job_id,
            "state": status.get("state"),
            "messageCount": message_count,
            "recordCount": record_count,
            "returned": len(rows),
            "kind": kind,
            "query": args.query,
            "from": from_ms,
            "to": to_ms,
            "results": rows,
            "pendingErrors": status.get("pendingErrors") or [],
            "pendingWarnings": status.get("pendingWarnings") or [],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    finally:
        if not args.keep_job:
            delete_job(client, job_id)


if __name__ == "__main__":
    main()
