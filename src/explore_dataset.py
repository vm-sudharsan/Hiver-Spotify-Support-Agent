"""Chunked, read-only exploration of the Twitter Customer Support dataset.

The source CSV is never changed.  A temporary SQLite index is used only while
the report is being produced, so the process stays bounded in RAM.
"""
from __future__ import annotations

import argparse
import csv
import os
import sqlite3
import tempfile
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


FIELDS = [
    "tweet_id", "author_id", "inbound", "created_at", "text",
    "response_tweet_id", "in_response_to_tweet_id",
]
CHUNK_SIZE = 50_000
DATE_FORMAT = "%a %b %d %H:%M:%S %z %Y"


def value(row: dict[str, str], name: str) -> str:
    return (row.get(name) or "").strip()


def write_report(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path,
                        default=Path(r"D:\Hiver\data\raw\archive\twcs.csv"))
    parser.add_argument("--report", type=Path,
                        default=Path(r"D:\Hiver\reports\DATASET_EXPLORATION.md"))
    parser.add_argument("--keep-index", action="store_true",
                        help="Keep the temporary SQLite index for debugging.")
    args = parser.parse_args()
    source, report = args.input, args.report
    if not source.is_file():
        raise FileNotFoundError(source)

    started = time.perf_counter()
    report.parent.mkdir(parents=True, exist_ok=True)
    index_fd, index_name = tempfile.mkstemp(prefix="twcs_explore_", suffix=".sqlite",
                                             dir=report.parent)
    os.close(index_fd)
    index_path = Path(index_name)

    conn = sqlite3.connect(index_path)
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA temp_store=FILE")
    conn.execute("PRAGMA cache_size=-32768")  # approximately 32 MiB
    conn.execute("""CREATE TABLE messages (
        tweet_id TEXT PRIMARY KEY, author_id TEXT NOT NULL, inbound INTEGER NOT NULL,
        created_at TEXT NOT NULL, response_id TEXT, parent_id TEXT
    ) WITHOUT ROWID""")

    rows = 0
    missing = Counter()
    inbound_counts = Counter()
    outbound_volume = Counter()
    min_date = max_date = None
    with source.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            print("Warning: unexpected column order:", reader.fieldnames)
        batch = []
        for row in reader:
            rows += 1
            for field in FIELDS:
                if not value(row, field):
                    missing[field] += 1
            inbound = value(row, "inbound").lower() == "true"
            inbound_counts["inbound" if inbound else "outbound"] += 1
            author = value(row, "author_id")
            if not inbound:
                outbound_volume[author] += 1
            try:
                date = datetime.strptime(value(row, "created_at"), DATE_FORMAT)
                min_date = date if min_date is None or date < min_date else min_date
                max_date = date if max_date is None or date > max_date else max_date
            except ValueError:
                pass
            batch.append((value(row, "tweet_id"), author, int(inbound),
                          value(row, "created_at"), value(row, "response_tweet_id"),
                          value(row, "in_response_to_tweet_id")))
            if len(batch) >= CHUNK_SIZE:
                conn.executemany("INSERT OR REPLACE INTO messages VALUES (?, ?, ?, ?, ?, ?)", batch)
                conn.commit()
                batch.clear()
        if batch:
            conn.executemany("INSERT OR REPLACE INTO messages VALUES (?, ?, ?, ?, ?, ?)", batch)
            conn.commit()

    # These indexes support direct relationship validation and thread walks.
    conn.execute("CREATE INDEX idx_messages_parent ON messages(parent_id)")
    conn.execute("CREATE INDEX idx_messages_response ON messages(response_id)")
    conn.execute("CREATE INDEX idx_messages_outbound ON messages(inbound, author_id)")
    conn.commit()

    # Relationship quality: both fields should describe inverse sides of an edge.
    response_present = conn.execute("SELECT COUNT(*) FROM messages WHERE response_id <> ''").fetchone()[0]
    parent_present = conn.execute("SELECT COUNT(*) FROM messages WHERE parent_id <> ''").fetchone()[0]
    response_targets_present = conn.execute("""SELECT COUNT(*) FROM messages m
        JOIN messages t ON t.tweet_id=m.response_id WHERE m.response_id<>''""").fetchone()[0]
    parent_targets_present = conn.execute("""SELECT COUNT(*) FROM messages m
        JOIN messages t ON t.tweet_id=m.parent_id WHERE m.parent_id<>''""").fetchone()[0]
    reciprocal_response = conn.execute("""SELECT COUNT(*) FROM messages m
        JOIN messages t ON t.tweet_id=m.response_id
        WHERE m.response_id<>'' AND t.parent_id=m.tweet_id""").fetchone()[0]
    reciprocal_parent = conn.execute("""SELECT COUNT(*) FROM messages m
        JOIN messages t ON t.tweet_id=m.parent_id
        WHERE m.parent_id<>'' AND t.response_id=m.tweet_id""").fetchone()[0]

    # A reconstructable support thread starts with a customer post whose declared
    # response is an outbound company post. Descendants are followed by parent_id.
    # This is deliberately conservative: it avoids pretending external/missing
    # links are complete conversations.
    conn.execute("""CREATE TABLE rooted_threads AS
      WITH RECURSIVE chain(root_id, company, tweet_id, depth) AS (
        SELECT m.tweet_id, reply.author_id, m.tweet_id, 0
        FROM messages m JOIN messages reply ON reply.tweet_id=m.response_id
        WHERE m.inbound=1 AND m.parent_id='' AND reply.inbound=0
        UNION ALL
        SELECT c.root_id, c.company, child.tweet_id, c.depth+1
        FROM chain c JOIN messages child ON child.parent_id=c.tweet_id
        WHERE c.depth < 100
      )
      SELECT root_id, company, COUNT(*) AS messages,
             SUM(CASE WHEN m.inbound=1 THEN 1 ELSE 0 END) AS customer_messages,
             SUM(CASE WHEN m.inbound=0 THEN 1 ELSE 0 END) AS company_messages,
             CASE WHEN SUM(CASE WHEN m.inbound=1 THEN 1 ELSE 0 END)>=2
                    AND SUM(CASE WHEN m.inbound=0 THEN 1 ELSE 0 END)>=2
                  THEN 1 ELSE 0 END AS multi_turn
      FROM chain JOIN messages m ON m.tweet_id=chain.tweet_id
      GROUP BY root_id, company""")
    conn.execute("CREATE INDEX idx_threads_company ON rooted_threads(company)")
    conn.commit()

    thread_stats = conn.execute("""SELECT company, COUNT(*) threads,
        SUM(messages) total_messages, SUM(customer_messages) customer_messages,
        SUM(company_messages) company_messages, AVG(messages) avg_messages,
        AVG(multi_turn)*100 multi_turn_pct
      FROM rooted_threads GROUP BY company ORDER BY threads DESC, total_messages DESC""").fetchall()
    top = thread_stats[:20]
    stats_by_company = {r[0]: r for r in thread_stats}

    # Directly linked inbound messages are a useful coverage diagnostic, but are
    # not used for ranking because a single thread can have many such messages.
    direct_inbound = dict(conn.execute("""SELECT o.author_id, COUNT(DISTINCT i.tweet_id)
      FROM messages o JOIN messages i
        ON (i.response_id=o.tweet_id OR i.parent_id=o.tweet_id)
      WHERE o.inbound=0 AND i.inbound=1 GROUP BY o.author_id"""))

    lines = [
        "# TWCS Dataset Exploration",
        "",
        "Generated by `src/explore_dataset.py` using chunked CSV reads and a temporary disk-backed SQLite index. The raw dataset was not modified.",
        "",
        "## A. Dataset overview",
        "",
        f"- Source: `{source}`",
        f"- Rows: **{rows:,}**",
        f"- Columns: {', '.join(FIELDS)}",
        "- CSV storage types: all fields are text; inferred semantic types are: `tweet_id`/relationship IDs = identifiers, `inbound` = boolean, `created_at` = timestamp, `author_id`/`text` = text.",
        f"- Date range: **{min_date.isoformat() if min_date else 'unparsed'}** to **{max_date.isoformat() if max_date else 'unparsed'}**",
        f"- Inbound customer tweets: **{inbound_counts['inbound']:,}**; outbound company tweets: **{inbound_counts['outbound']:,}**.",
        f"- Unique outbound support accounts: **{len(outbound_volume):,}**.",
        "",
        "## B. Data quality issues",
        "",
        "| Field | Missing values |",
        "|---|---:|",
        *[f"| `{field}` | {missing[field]:,} |" for field in FIELDS],
        "",
        f"- `response_tweet_id` is populated for {response_present:,} tweets; {response_targets_present:,} ({response_targets_present / response_present * 100 if response_present else 0:.1f}%) target a row in this file.",
        f"- `in_response_to_tweet_id` is populated for {parent_present:,} tweets; {parent_targets_present:,} ({parent_targets_present / parent_present * 100 if parent_present else 0:.1f}%) target a row in this file.",
        f"- Exact reciprocal links occur for {reciprocal_response:,} response links and {reciprocal_parent:,} parent links. Missing/external counterpart rows mean complete reconstruction is not guaranteed.",
        "",
        "## C. Conversation/thread structure",
        "",
        "A **reconstructable rooted support thread** is conservatively defined as an inbound tweet with no in-file parent whose `response_tweet_id` points to an outbound tweet; descendants are followed through `in_response_to_tweet_id` (maximum depth 100). A **multi-turn** thread has at least two customer and two company messages. This intentionally undercounts conversations that begin outside the export or have missing links.",
        f"- Reconstructable rooted threads: **{sum(r[1] for r in thread_stats):,}**.",
        f"- Multi-turn rooted threads: **{sum(round(r[1] * r[6] / 100) for r in thread_stats):,}** (rounded from per-company aggregates).",
        "- `response_tweet_id` points forward to a reply; `in_response_to_tweet_id` points back to the parent. They are often reciprocal, but neither is complete enough by itself to claim all connected components are complete conversations.",
        "",
        "## D. Top companies by support conversation volume",
        "",
        "Ranked by reconstructable rooted support threads, **not** raw tweet count.",
        "",
        "| Rank | Support account | Threads | Thread messages | Customer | Company | Avg msgs/thread | Multi-turn | Full outbound volume | Directly linked customer msgs |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, r in enumerate(top, 1):
        company, threads, total, customer, company_msgs, average, multi = r
        lines.append(f"| {rank} | @{company} | {threads:,} | {total:,} | {customer:,} | {company_msgs:,} | {average:.2f} | {multi:.1f}% | {outbound_volume[company]:,} | {direct_inbound.get(company, 0):,} |")

    candidates = top[:10]
    lines += ["", "## E. Candidate brands for the project", "",
              "These are provisional candidates selected from the highest reconstructable-thread volumes. No final brand selection is made here.", ""]
    for company, threads, total, customer, company_msgs, average, multi in candidates:
        lines.append(f"### @{company}")
        lines.append(f"- **Evidence:** {threads:,} reconstructable threads, {total:,} messages, {average:.2f} messages/thread, and {multi:.1f}% multi-turn.")
        if multi >= 20 and threads >= 1_000:
            reason = "Strong candidate: substantial volume and enough back-and-forth to evaluate conversational handling."
        elif threads >= 1_000:
            reason = "Viable volume candidate, but the low multi-turn share may limit context-heavy evaluation."
        else:
            reason = "Worth sampling, but smaller reconstructable volume means it should be compared with higher-volume accounts."
        lines.append(f"- **Suitability:** {reason}")
        lines.append("")

    lines += [
        "## F. Why suitability still needs validation",
        "",
        "The candidate list measures structure and volume, not topic quality, language consistency, privacy risk, domain fit, or whether support replies are useful rather than boilerplate. High volume alone is not a recommendation.",
        "",
        "## G. Questions for deeper investigation before selecting a final brand",
        "",
        "1. Are the candidate's conversations mostly English and sufficiently clean for the assignment?",
        "2. What are the common intent categories, and are there enough examples of each?",
        "3. How often do conversations contain sensitive personal data, URLs, or hand-offs to DMs?",
        "4. Are multi-turn threads semantically coherent when sampled, rather than only structurally linked?",
        "5. Does one account dominate a narrow issue type or contain varied support scenarios?",
        "6. What response-quality target and evaluation split can be made without leakage across a thread?",
        "",
        f"Analysis runtime: {time.perf_counter() - started:.1f} seconds.",
    ]
    write_report(report, lines)
    conn.close()
    if args.keep_index:
        print(f"Temporary index retained: {index_path}")
    else:
        index_path.unlink(missing_ok=True)
    print(f"Report written: {report}")
    print(f"Rows processed: {rows:,}")
    print(f"Elapsed seconds: {time.perf_counter() - started:.1f}")


if __name__ == "__main__":
    main()
