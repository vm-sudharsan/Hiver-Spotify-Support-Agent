"""Build a provenance-preserving SpotifyCares journey pool from TWCS.

The raw CSV is read in bounded batches into a temporary SQLite index. The raw
file is never changed. No taxonomy labels are assigned by this script.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import tempfile
import time
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path


FIELDS = [
    "tweet_id",
    "author_id",
    "inbound",
    "created_at",
    "text",
    "response_tweet_id",
    "in_response_to_tweet_id",
]
DEFAULT_INPUT = Path(r"D:\Hiver\data\raw\archive\twcs.csv")
DEFAULT_OUTPUT = Path(r"D:\Hiver\data\processed\spotify_journeys.jsonl")
DEFAULT_MANIFEST = Path(r"D:\Hiver\data\processed\spotify_journeys_manifest.json")
CHUNK_SIZE = 50_000
MAX_DEPTH = 100
BRAND = "SpotifyCares"
DATE_FORMAT = "%a %b %d %H:%M:%S %z %Y"

FAILURE_RE = re.compile(
    r"\b(no luck|still(?: not| no| having)|didn['’]?t help|did not help|"
    r"nothing changed|neither worked|won['’]?t work|doesn['’]?t work|"
    r"still happens|problem persists|cannot|can't)\b",
    re.IGNORECASE,
)
QUESTION_RE = re.compile(r"\?|\b(?:what|which|where|when|how|can you|could you|are you)\b", re.IGNORECASE)
DIAGNOSTIC_RE = re.compile(
    r"\b(?:device|operating system|\bios\b|\bandroid\b|version|browser|"
    r"screenshot|error message|wifi|wi-fi|cellular|3g|4g|network|country|"
    r"song link|song uri|username|email address|what .* version)\b",
    re.IGNORECASE,
)
DM_RE = re.compile(r"\b(?:dm|direct message|private message|secure|username|email address)\b", re.IGNORECASE)
RESOLUTION_RE = re.compile(
    r"\b(?:fixed|resolved|working now|works now|it works|worked|solved|"
    r"glad to hear|thank(?:s| you).*(?:worked|helped|fixed))\b",
    re.IGNORECASE,
)


def clean(row: dict[str, str], name: str) -> str:
    return (row.get(name) or "").strip()


def normalized_text(text: str) -> str:
    value = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(value.split())


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_timestamp(value: str) -> str:
    try:
        return datetime.strptime(value, DATE_FORMAT).isoformat()
    except ValueError:
        return ""


def message_flags(text: str) -> dict[str, bool]:
    return {
        "failure_marker_flag": bool(FAILURE_RE.search(text)),
        "question_marker_flag": bool(QUESTION_RE.search(text)),
        "diagnostic_context_marker_flag": bool(DIAGNOSTIC_RE.search(text)),
        "dm_handoff_marker_flag": bool(DM_RE.search(text)),
        "resolution_marker_flag": bool(RESOLUTION_RE.search(text)),
    }


def setup_database(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA temp_store=FILE")
    conn.execute("PRAGMA cache_size=-32768")
    conn.execute(
        """CREATE TABLE messages (
            tweet_id TEXT PRIMARY KEY,
            author_id TEXT NOT NULL,
            inbound INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            created_at_sort TEXT NOT NULL,
            text TEXT NOT NULL,
            response_tweet_id TEXT NOT NULL,
            in_response_to_tweet_id TEXT NOT NULL,
            exact_hash TEXT NOT NULL,
            normalized_hash TEXT NOT NULL
        ) WITHOUT ROWID"""
    )
    return conn


def ingest(source: Path, conn: sqlite3.Connection) -> tuple[int, Counter, float]:
    started = time.perf_counter()
    rows = 0
    invalid_dates = 0
    inbound_counts = Counter()
    batch: list[tuple[str, ...]] = []
    with source.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"Unexpected CSV columns: {reader.fieldnames!r}")
        for row in reader:
            rows += 1
            tweet_id = clean(row, "tweet_id")
            if not tweet_id:
                raise ValueError(f"Row {rows} has an empty tweet_id")
            author_id = clean(row, "author_id")
            inbound_value = clean(row, "inbound").casefold()
            if inbound_value not in {"true", "false"}:
                raise ValueError(f"Row {rows} has invalid inbound value: {inbound_value!r}")
            inbound = int(inbound_value == "true")
            created_at = clean(row, "created_at")
            created_at_sort = parse_timestamp(created_at)
            invalid_dates += not bool(created_at_sort)
            text = clean(row, "text")
            response_id = clean(row, "response_tweet_id")
            parent_id = clean(row, "in_response_to_tweet_id")
            exact_value = "\x1f".join((str(inbound), author_id, text))
            normalized_value = "\x1f".join((str(inbound), author_id.casefold(), normalized_text(text)))
            batch.append(
                (
                    tweet_id,
                    author_id,
                    inbound,
                    created_at,
                    created_at_sort,
                    text,
                    response_id,
                    parent_id,
                    digest(exact_value),
                    digest(normalized_value),
                )
            )
            inbound_counts["customer" if inbound else "support"] += 1
            if len(batch) >= CHUNK_SIZE:
                conn.executemany("INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", batch)
                conn.commit()
                batch.clear()
                if rows % 500_000 == 0:
                    print(f"Indexed {rows:,} raw rows...")
        if batch:
            conn.executemany("INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", batch)
            conn.commit()
    conn.execute("CREATE INDEX idx_messages_parent ON messages(in_response_to_tweet_id)")
    conn.execute("CREATE INDEX idx_messages_response ON messages(response_tweet_id)")
    conn.execute("CREATE INDEX idx_messages_author_inbound ON messages(author_id, inbound)")
    conn.execute("CREATE INDEX idx_messages_exact_hash ON messages(exact_hash)")
    conn.execute("CREATE INDEX idx_messages_normalized_hash ON messages(normalized_hash)")
    conn.commit()
    inbound_counts["invalid_dates"] = invalid_dates
    return rows, inbound_counts, time.perf_counter() - started


def duplicate_counts(conn: sqlite3.Connection) -> tuple[dict[str, int], dict[str, int]]:
    exact = {
        row[0]: row[1]
        for row in conn.execute("SELECT exact_hash, COUNT(*) FROM messages GROUP BY exact_hash")
    }
    normalized = {
        row[0]: row[1]
        for row in conn.execute("SELECT normalized_hash, COUNT(*) FROM messages GROUP BY normalized_hash")
    }
    return exact, normalized


def root_rows(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    return conn.execute(
        """SELECT m.tweet_id, reply.author_id
           FROM messages m
           JOIN messages reply ON reply.tweet_id = m.response_tweet_id
           WHERE m.inbound = 1
             AND m.in_response_to_tweet_id = ''
             AND reply.inbound = 0
             AND reply.author_id = ?
           ORDER BY m.tweet_id""",
        (BRAND,),
    ).fetchall()


def journey_rows(conn: sqlite3.Connection, root_id: str) -> list[tuple]:
    return conn.execute(
        """WITH RECURSIVE chain(tweet_id, depth, path) AS (
               SELECT ?, 0, '|' || ? || '|'
               UNION ALL
               SELECT child.tweet_id, chain.depth + 1,
                      chain.path || child.tweet_id || '|'
               FROM chain
               JOIN messages child ON child.in_response_to_tweet_id = chain.tweet_id
               WHERE chain.depth < ?
                 AND instr(chain.path, '|' || child.tweet_id || '|') = 0
           )
           SELECT chain.depth, m.tweet_id, m.author_id, m.inbound,
                  m.created_at, m.created_at_sort, m.text,
                  m.in_response_to_tweet_id, m.response_tweet_id,
                  m.exact_hash, m.normalized_hash
           FROM chain JOIN messages m ON m.tweet_id = chain.tweet_id
           ORDER BY chain.depth, m.created_at_sort, m.created_at, m.tweet_id""",
        (root_id, root_id, MAX_DEPTH),
    ).fetchall()


def has_child_at_depth(conn: sqlite3.Connection, rows: list[tuple]) -> bool:
    depth_ids = {row[1] for row in rows if row[0] == MAX_DEPTH}
    if not depth_ids:
        return False
    placeholders = ",".join("?" for _ in depth_ids)
    query = f"SELECT 1 FROM messages WHERE in_response_to_tweet_id IN ({placeholders}) LIMIT 1"
    return conn.execute(query, tuple(depth_ids)).fetchone() is not None


def reconstruction_status(conn: sqlite3.Connection, rows: list[tuple], depth_limited: bool) -> tuple[str, list[str]]:
    ids = {row[1] for row in rows}
    reasons: list[str] = []
    missing_link = False
    inconsistent_link = False
    for depth, tweet_id, _author, _inbound, _created, _sort, _text, parent_id, response_id, *_ in rows:
        for relation_name, target_id in (("parent", parent_id), ("response", response_id)):
            if target_id and not conn.execute("SELECT 1 FROM messages WHERE tweet_id = ?", (target_id,)).fetchone():
                missing_link = True
                reasons.append(f"missing_{relation_name}_target")
        if parent_id and parent_id not in ids:
            missing_link = True
        if parent_id:
            parent_response = conn.execute(
                "SELECT response_tweet_id FROM messages WHERE tweet_id = ?", (parent_id,)
            ).fetchone()
            if parent_response and parent_response[0] and parent_response[0] != tweet_id:
                inconsistent_link = True
                reasons.append("non_reciprocal_parent_link")
    if depth_limited:
        reasons.append("depth_limit_reached")
        return "partial", sorted(set(reasons))
    if missing_link:
        return "partial", sorted(set(reasons))
    if inconsistent_link:
        return "uncertain", sorted(set(reasons))
    return "complete", []


def build_journey(conn: sqlite3.Connection, root_id: str, exact_counts: dict[str, int], normalized_counts: dict[str, int]) -> dict:
    rows = journey_rows(conn, root_id)
    if not rows or rows[0][1] != root_id:
        raise ValueError(f"Root {root_id} was not reconstructed")
    depth_limited = has_child_at_depth(conn, rows)
    status, status_reasons = reconstruction_status(conn, rows, depth_limited)
    ordered = sorted(rows, key=lambda row: (row[5] or "\uffff", row[4], row[1]))
    messages = []
    flags = Counter()
    for depth, tweet_id, author_id, inbound, created_at, created_at_sort, text, parent_id, response_id, exact_hash, normalized_hash in ordered:
        message_flag_values = message_flags(text)
        flags.update({name: value for name, value in message_flag_values.items() if value})
        messages.append(
            {
                "tweet_id": tweet_id,
                "author_id": author_id,
                "inbound": bool(inbound),
                "role": "customer" if inbound else "support",
                "created_at": created_at,
                "text": text,
                "in_response_to_tweet_id": parent_id,
                "response_tweet_id": response_id,
                "reconstruction_depth": depth,
                "exact_duplicate_message": exact_counts[exact_hash] > 1,
                "exact_duplicate_message_count": exact_counts[exact_hash],
                "normalized_duplicate_message": normalized_counts[normalized_hash] > 1,
                "normalized_duplicate_message_count": normalized_counts[normalized_hash],
                "heuristic_flags": message_flag_values,
            }
        )
    exact_signature = digest("\x1e".join(f"{m['role']}\x1f{m['text']}" for m in messages))
    normalized_signature = digest(
        "\x1e".join(f"{m['role']}\x1f{normalized_text(m['text'])}" for m in messages)
    )
    customer_count = sum(m["role"] == "customer" for m in messages)
    support_count = sum(m["role"] == "support" for m in messages)
    journey_id = f"spotifycares-{root_id}"
    return {
        "journey_id": journey_id,
        "root_tweet_id": root_id,
        "brand": BRAND,
        "reconstruction_status": status,
        "reconstruction_status_reasons": status_reasons,
        "message_count": len(messages),
        "customer_turn_count": customer_count,
        "support_turn_count": support_count,
        "multi_turn": customer_count >= 2 and support_count >= 2,
        "started_at": min((m["created_at"] for m in messages), default=""),
        "ended_at": max((m["created_at"] for m in messages), default=""),
        "heuristic_metadata": {
            "failure_marker_flag": bool(flags["failure_marker_flag"]),
            "question_marker_flag": bool(flags["question_marker_flag"]),
            "diagnostic_context_marker_flag": bool(flags["diagnostic_context_marker_flag"]),
            "dm_handoff_marker_flag": bool(flags["dm_handoff_marker_flag"]),
            "resolution_marker_flag": bool(flags["resolution_marker_flag"]),
        },
        "duplicate_leakage_metadata": {
            "journey_signature_exact_hash": exact_signature,
            "journey_signature_normalized_hash": normalized_signature,
            "exact_duplicate_journey_signature_count": 0,
            "normalized_duplicate_journey_signature_count": 0,
            "exact_duplicate_journey_signature": False,
            "normalized_duplicate_journey_signature": False,
            "semantic_near_duplicate_detection": "not_implemented",
        },
        "messages": messages,
    }


def update_journey_duplicate_metadata(journeys: list[dict]) -> None:
    exact_counts = Counter(j["duplicate_leakage_metadata"]["journey_signature_exact_hash"] for j in journeys)
    normalized_counts = Counter(j["duplicate_leakage_metadata"]["journey_signature_normalized_hash"] for j in journeys)
    for journey in journeys:
        metadata = journey["duplicate_leakage_metadata"]
        exact_count = exact_counts[metadata["journey_signature_exact_hash"]]
        normalized_count = normalized_counts[metadata["journey_signature_normalized_hash"]]
        metadata["exact_duplicate_journey_signature_count"] = exact_count
        metadata["normalized_duplicate_journey_signature_count"] = normalized_count
        metadata["exact_duplicate_journey_signature"] = exact_count > 1
        metadata["normalized_duplicate_journey_signature"] = normalized_count > 1


def validate_journeys(journeys: list[dict], output: Path) -> dict[str, int]:
    journey_ids = [j["journey_id"] for j in journeys]
    if len(journey_ids) != len(set(journey_ids)):
        raise ValueError("Journey IDs are not unique")
    status_counts = Counter()
    message_count = 0
    customer_count = 0
    support_count = 0
    multi_turn_count = 0
    for journey in journeys:
        status_counts[journey["reconstruction_status"]] += 1
        message_ids = {m["tweet_id"] for m in journey["messages"]}
        if len(message_ids) != len(journey["messages"]):
            raise ValueError(f"Duplicate tweet IDs within {journey['journey_id']}")
        if journey["message_count"] != len(journey["messages"]):
            raise ValueError(f"Message count mismatch in {journey['journey_id']}")
        if journey["customer_turn_count"] + journey["support_turn_count"] != journey["message_count"]:
            raise ValueError(f"Turn count mismatch in {journey['journey_id']}")
        for message in journey["messages"]:
            if not message["tweet_id"]:
                raise ValueError(f"Empty tweet ID in {journey['journey_id']}")
            expected_role = "customer" if message["inbound"] else "support"
            if message["role"] != expected_role:
                raise ValueError(f"Role/inbound mismatch for {message['tweet_id']}")
            if message["tweet_id"] != journey["root_tweet_id"] and message["in_response_to_tweet_id"] not in message_ids:
                raise ValueError(
                    f"Non-root parent was not retained in {journey['journey_id']}: "
                    f"{message['tweet_id']} -> {message['in_response_to_tweet_id']}"
                )
        ordered_keys = [
            (parse_timestamp(m["created_at"]) or "\uffff", m["created_at"], m["tweet_id"])
            for m in journey["messages"]
        ]
        if ordered_keys != sorted(ordered_keys):
            raise ValueError(f"Message ordering is not deterministic in {journey['journey_id']}")
        message_count += journey["message_count"]
        customer_count += journey["customer_turn_count"]
        support_count += journey["support_turn_count"]
        multi_turn_count += journey["multi_turn"]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for journey in journeys:
            handle.write(json.dumps(journey, ensure_ascii=False, sort_keys=True) + "\n")
    read_back = 0
    with output.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            json.loads(line)
            read_back += 1
    if read_back != len(journeys):
        raise ValueError(f"Read-back count {read_back} does not match {len(journeys)}")
    return {
        "journey_count": len(journeys),
        "complete_journeys": status_counts["complete"],
        "partial_journeys": status_counts["partial"],
        "uncertain_journeys": status_counts["uncertain"],
        "message_count": message_count,
        "customer_turn_count": customer_count,
        "support_turn_count": support_count,
        "multi_turn_journeys": multi_turn_count,
        "read_back_journeys": read_back,
    }


def write_manifest(path: Path, stats: dict, source: Path, output: Path, ingest_seconds: float, elapsed_seconds: float) -> None:
    manifest = {
        "input_dataset": str(source),
        "output_dataset": str(output),
        "brand_filter": BRAND,
        "root_definition": "inbound root with empty in-file parent and response_tweet_id targeting outbound SpotifyCares support",
        "descendant_definition": "follow in_response_to_tweet_id children through depth 100",
        "max_depth": MAX_DEPTH,
        "standard_library_hash": "sha256",
        "semantic_near_duplicate_detection": "not_implemented; exact and normalized deterministic hashes only",
        "statistics": stats,
        "ingest_seconds": round(ingest_seconds, 3),
        "total_runtime_seconds": round(elapsed_seconds, 3),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Raw TWCS CSV path")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Journey JSONL output path")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="Manifest JSON path")
    parser.add_argument("--keep-index", action="store_true", help="Keep the temporary SQLite index")
    args = parser.parse_args()
    source = args.input.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Input dataset does not exist: {source}")
    started = time.perf_counter()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    index_fd, index_name = tempfile.mkstemp(prefix="spotify_journeys_", suffix=".sqlite", dir=args.output.parent)
    os.close(index_fd)
    index_path = Path(index_name)
    conn = None
    try:
        conn = setup_database(index_path)
        print(f"Indexing raw dataset in chunks: {source}")
        rows, input_stats, ingest_seconds = ingest(source, conn)
        print(f"Indexed {rows:,} rows in {ingest_seconds:.1f}s; selecting {BRAND} roots...")
        exact_counts, normalized_counts = duplicate_counts(conn)
        roots = root_rows(conn)
        print(f"Found {len(roots):,} reconstructable {BRAND} roots")
        journeys = []
        for index, (root_id, _company) in enumerate(roots, 1):
            journeys.append(build_journey(conn, root_id, exact_counts, normalized_counts))
            if index % 5_000 == 0:
                print(f"Reconstructed {index:,}/{len(roots):,} journeys...")
        update_journey_duplicate_metadata(journeys)
        stats = validate_journeys(journeys, args.output)
        stats["input_rows"] = rows
        stats["input_customer_rows"] = input_stats["customer"]
        stats["input_support_rows"] = input_stats["support"]
        stats["invalid_created_at_rows"] = input_stats["invalid_dates"]
        elapsed = time.perf_counter() - started
        write_manifest(args.manifest, stats, source, args.output, ingest_seconds, elapsed)
        print(json.dumps(stats, indent=2))
        print(f"Journey dataset written: {args.output}")
        print(f"Manifest written: {args.manifest}")
        print(f"Elapsed seconds: {elapsed:.1f}")
    finally:
        if conn is not None:
            conn.close()
        if args.keep_index:
            print(f"Temporary SQLite index retained: {index_path}")
        else:
            index_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
