"""
Deterministic aggregates for /report/* — all counts from stored incidents, not the LLM.
"""
from __future__ import annotations

import csv
import io
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

TRUST_BUCKETS = [(0, 40), (40, 60), (60, 80), (80, 101)]


def _bucket_label(lo: int, hi: int) -> str:
    return f"{lo}-{hi - 1}" if hi < 101 else f"{lo}+"


def _floor_bucket(ts: float, bucket_seconds: int) -> int:
    return int(ts // bucket_seconds * bucket_seconds)


def incidents_in_window(
    incidents: List[Dict[str, Any]],
    start_ts: float,
    end_ts: float,
) -> List[Dict[str, Any]]:
    out = []
    for inc in incidents:
        t = float(inc.get("observed_at") or 0)
        if start_ts <= t < end_ts:
            out.append(inc)
    return out


def _series_over_time(
    rows: List[Dict[str, Any]],
    start_ts: float,
    end_ts: float,
    bucket_seconds: int,
) -> List[Dict[str, Any]]:
    """Counts per time bucket by severity."""
    by_bucket: Dict[int, Dict[str, int]] = defaultdict(
        lambda: {"high": 0, "medium": 0, "low": 0, "total": 0}
    )
    for inc in rows:
        t = float(inc.get("observed_at") or 0)
        b = _floor_bucket(t, bucket_seconds)
        sev = (inc.get("severity") or "low").lower()
        if sev not in by_bucket[b]:
            sev = "low"
        by_bucket[b][sev] = by_bucket[b].get(sev, 0) + 1
        by_bucket[b]["total"] += 1
    keys = sorted(k for k in by_bucket if start_ts <= k < end_ts)
    out = []
    for k in keys:
        d = by_bucket[k]
        out.append(
            {
                "t": k,
                "label": datetime.fromtimestamp(k, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                if bucket_seconds < 86400
                else datetime.fromtimestamp(k, tz=timezone.utc).strftime("%Y-%m-%d"),
                "high": d["high"],
                "medium": d["medium"],
                "low": d["low"],
                "total": d["total"],
            }
        )
    return out


def _series_by_type(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    c = Counter((r.get("type") or "general").lower() for r in rows)
    return [{"type": k, "count": v} for k, v in c.most_common(20)]


def _trust_distribution(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts = { _bucket_label(lo, hi): 0 for lo, hi in TRUST_BUCKETS}
    for r in rows:
        try:
            ts = int(r.get("trustScore") or 0)
        except (TypeError, ValueError):
            ts = 0
        for lo, hi in TRUST_BUCKETS:
            if lo <= ts < hi:
                counts[_bucket_label(lo, hi)] += 1
                break
    return [{"range": k, "count": v} for k, v in counts.items()]


def _top_sources(rows: List[Dict[str, Any]], n: int = 12) -> List[Dict[str, Any]]:
    c = Counter((r.get("source") or "Unknown").strip() or "Unknown" for r in rows)
    return [{"source": k, "count": v} for k, v in c.most_common(n)]


def _totals(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_sev = Counter((r.get("severity") or "low").lower() for r in rows)
    return {
        "count": len(rows),
        "by_severity": dict(by_sev),
        "by_type": dict(Counter((r.get("type") or "general").lower() for r in rows)),
    }


def _pick_bucket_seconds(hours: float) -> int:
    if hours <= 48:
        return 3600
    return 86400


def build_window_payload(
    all_incidents: List[Dict[str, Any]],
    hours: float,
    end_ts: Optional[float] = None,
) -> Dict[str, Any]:
    end = end_ts if end_ts is not None else time.time()
    start = end - hours * 3600
    rows = incidents_in_window(all_incidents, start, end)
    bucket_sec = _pick_bucket_seconds(hours)
    series_time = _series_over_time(rows, start, end, bucket_sec)
    peak = None
    if series_time:
        peak = max(series_time, key=lambda x: x["total"])
    return {
        "start_ts": start,
        "end_ts": end,
        "hours": hours,
        "totals": _totals(rows),
        "series_severity_time": series_time,
        "series_by_type": _series_by_type(rows),
        "trust_distribution": _trust_distribution(rows),
        "top_sources": _top_sources(rows),
        "peak_bucket": peak,
        "incident_ids": [r.get("id") for r in rows if r.get("id") is not None],
    }


def build_summary(
    all_incidents: List[Dict[str, Any]],
    hours: float = 24,
    compare_hours: Optional[float] = None,
) -> Dict[str, Any]:
    now = time.time()
    primary = build_window_payload(all_incidents, hours, end_ts=now)
    compare_block = None
    if compare_hours and compare_hours > 0:
        compare_end = now - hours * 3600
        compare_block = build_window_payload(all_incidents, compare_hours, end_ts=compare_end)
        compare_block["label"] = f"previous_{compare_hours}h_before_primary"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "primary": primary,
        "compare": compare_block,
    }


def incidents_to_csv_rows(rows: List[Dict[str, Any]]) -> str:
    buf = io.StringIO()
    fields = [
        "id",
        "observed_at",
        "timestamp",
        "title",
        "severity",
        "points",
        "trustScore",
        "type",
        "source",
        "location",
        "url",
        "description",
    ]
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        line = {k: r.get(k, "") for k in fields}
        oa = r.get("observed_at")
        if isinstance(oa, (int, float)):
            line["observed_at"] = datetime.fromtimestamp(float(oa), tz=timezone.utc).isoformat()
        w.writerow(line)
    return buf.getvalue()


def build_print_html(summary: Dict[str, Any], incidents_sample: List[Dict[str, Any]]) -> str:
    p = summary["primary"]
    tot = p["totals"]
    rows_html = "".join(
        f"<tr><td>{_h(i.get('title',''))}</td><td>{_h(str(i.get('severity','')))}</td>"
        f"<td>{_h(str(i.get('source','')))}</td><td>{_h(str(i.get('timestamp','')))}</td></tr>"
        for i in incidents_sample[:50]
    )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>CrisisCompass report</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #111; }}
h1 {{ font-size: 1.25rem; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; font-size: 0.85rem; }}
th, td {{ border: 1px solid #ccc; padding: 0.35rem 0.5rem; text-align: left; }}
th {{ background: #f0f0f0; }}
.muted {{ color: #555; font-size: 0.9rem; margin-top: 0.5rem; }}
</style></head><body>
<h1>CrisisCompass — incident report</h1>
<p class="muted">Generated {_h(summary.get('generated_at',''))} · window: last {p.get('hours','')} h ·
incidents in window: {tot.get('count', 0)}</p>
<p class="muted">Severity breakdown: {_h(str(tot.get('by_severity', {})))}</p>
<p class="muted">This is decision-support from aggregated news signals, not an official emergency channel.</p>
<table>
<thead><tr><th>Title</th><th>Severity</th><th>Source</th><th>Timestamp</th></tr></thead>
<tbody>{rows_html}</tbody>
</table>
</body></html>"""


def _h(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
