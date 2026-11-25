#!/usr/bin/env python3
"""Deterministic, offline Granola CSV/ZIP parsing and Google Docs insertion plans."""
import argparse
import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from datetime import datetime, timezone as dt_timezone
from pathlib import Path
from uuid import UUID
from zoneinfo import ZoneInfo

FIELDS = ["document_id", "user_email", "document_title", "workspace_name", "document_created", "summary", "notes", "transcript"]
MAX_BYTES = 512 * 1024 * 1024

def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def utf16(value):
    return len(value.encode("utf-16-le")) // 2

def read_export(source, timezone="America/Los_Angeles"):
    csv.field_size_limit(MAX_BYTES)
    path = Path(source)
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            members = sorted(i for i in archive.infolist() if not i.is_dir() and i.filename.lower().endswith(".csv") and not i.filename.startswith("__MACOSX/"))
            if not members or sum(i.file_size for i in members) > MAX_BYTES:
                raise ValueError("No CSV members, or export exceeds 512 MiB limit")
            sources = [(i.filename, archive.read(i)) for i in members]
    else:
        if path.stat().st_size > MAX_BYTES:
            raise ValueError("Export exceeds 512 MiB limit")
        sources = [(path.name, path.read_bytes())]
    meetings = {}
    for name, data in sources:
        reader = csv.reader(io.StringIO(data.decode("utf-8-sig"), newline=""), strict=True)
        header = next(reader, None)
        if header != FIELDS:
            raise ValueError(f"{name}: unsupported header {header!r}; inspect schema, never guess delimiters")
        for row in reader:
            if len(row) != len(FIELDS):
                raise ValueError(f"{name}: physical line {reader.line_num}: expected 8 fields, found {len(row)}; no lossy repair allowed")
            record = dict(zip(FIELDS, row))
            mid = str(UUID(record["document_id"]))
            if mid != record["document_id"].lower():
                raise ValueError("Noncanonical Granola document ID")
            created = datetime.fromisoformat(record["document_created"].replace("Z", "+00:00"))
            if created.tzinfo is None:
                raise ValueError(f"{mid}: timestamp has no timezone")
            canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            item = {"schema_version": 1, "meeting_id": mid, "date": created.astimezone(ZoneInfo(timezone)).date().isoformat(), "date_source": "document_created", "timezone": timezone, "sort_timestamp": created.astimezone(dt_timezone.utc).isoformat(), "record_sha256": digest(canonical), "summary_sha256": digest(record["summary"]), "transcript_sha256": digest(record["transcript"]), "source_member": name, "source_record": record}
            if mid in meetings and meetings[mid]["record_sha256"] != item["record_sha256"]:
                raise ValueError(f"Conflicting rows for {mid}; resolve before importing")
            meetings[mid] = item
    return sorted(meetings.values(), key=lambda m: (m["sort_timestamp"], m["meeting_id"]), reverse=True)

PERSONAL_OVERRIDES = {"4996fe30-67c7-4af2-8863-0a0e8f2a2228"}

def is_personal(meeting):
    return bool(re.search(r"\[personal\]", meeting["source_record"]["document_title"], re.I)) or meeting["meeting_id"] in PERSONAL_OVERRIDES

def transcript_payload(meeting):
    """The archive contains only the join key and untouched transcript text."""
    return {"meeting_id": meeting["meeting_id"], "transcript": meeting["source_record"]["transcript"]}

def metadata_payload(meeting, tags, brief, **extra):
    """Centralize metadata in the organization ledger; do not duplicate raw text."""
    tags = sorted(set(str(t).strip().lower() for t in tags if str(t).strip()))
    if not tags or not brief.strip() or "\n" in brief:
        raise ValueError("Supply inferred tags and one-line meeting brief")
    metadata = {k: v for k, v in meeting.items() if k != "source_record"}
    record = meeting["source_record"]
    metadata.update({k: v for k, v in record.items() if k != "transcript"})
    metadata.pop("document_id", None)
    metadata.update(kind="personal" if is_personal(meeting) else "meeting", tags=tags, brief=brief.strip(), **extra)
    return metadata

def render_index(title, groups):
    """Human navigation: one organization line and one brief line per meeting."""
    lines = [title, ""]
    for group in sorted(groups, key=lambda x: (not x["organization"].startswith("0 -"), x["organization"].casefold())):
        meetings = sorted(group["meetings"].values(), key=lambda m: (m["sort_timestamp"], m["meeting_id"]), reverse=True)
        latest = meetings[0]["date"] if meetings else "No meetings yet"
        lines.append(f"{group['organization']} | Latest: {latest} | {group['organization_brief']} | {group['folder_url']}")
        for meeting in meetings:
            lines.append(f"  {meeting['date']} - {meeting['document_title']} | {meeting['brief']} | {group['notes_document_url']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def safe_name(value):
    return re.sub(r'[\x00-\x1f/\\]', "_", value).strip()[:100] or "Untitled"

def inline(value):
    # Render Markdown presentation only; never rewrite the source wording.
    value = re.sub(r"\[([^\]]+)\]\((https?://[^ )]+)\)", lambda m: m[1] if m[1] == m[2] else m[1] + " (" + m[2] + ")", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"\1", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", value)
    value = re.sub(r"`([^`]+)`", r"\1", value)
    return re.sub(r"\\([&~*_[\]`])", r"\1", value)

def section(meeting):
    record = meeting["source_record"]
    heading = meeting["date"] + " - " + record["document_title"]
    text = heading + "\n\n"
    styles = [(0, utf16(heading), "HEADING_1")]
    for line in record["summary"].splitlines():
        heading = re.match(r"^#{1,6} (.*)$", line)
        bullet = re.match(r"^( *)([-*]) (.*)$", line)
        start = utf16(text)
        if heading:
            line = inline(heading[1])
            styles.append((start, start + utf16(line), "HEADING_2"))
        elif bullet:
            line = bullet[1] + "• " + inline(bullet[3])
        else:
            line = inline(line)
        text += line + "\n"
    text += "\n"
    return text, styles, []

def named_positions(document):
    result = {}
    for key, item in document.get("namedRanges", {}).items():
        for named in item.get("namedRanges", []):
            name = named.get("name", key)
            if name.startswith("granola_") and named.get("ranges"):
                result[name[8:]] = named["ranges"][0]["startIndex"]
    for tab in document.get("tabs", []):
        result.update(named_positions(tab.get("documentTab", tab)))
        for child in tab.get("childTabs", []):
            result.update(named_positions({"tabs": [child]}))
    return result

def document_scope(document, tab_id):
    """Accept both raw Docs resources and the connector's flattened tab resources."""
    tabs = []
    def visit(items):
        for tab in items:
            tabs.append(tab)
            visit(tab.get("childTabs", []))
    visit(document.get("tabs", []))
    if not tabs:
        return document
    matches = [t for t in tabs if t.get("tabProperties", t).get("tabId") == tab_id] if tab_id else tabs
    if len(matches) != 1:
        raise ValueError("Resolve exactly one notes tab before planning changes")
    return matches[0].get("documentTab", matches[0])


def build_batch(new_meetings, document, existing, tab_id=None):
    """Insert missing sections without replacing existing text; support backfilled dates."""
    document = document_scope(document, tab_id)
    positions = named_positions(document)
    old = {m["meeting_id"]: m for m in existing}
    if set(positions) - set(old):
        raise ValueError("Named sections lack archived date metadata; reconcile before insertion")
    all_items = {**{mid: old[mid] for mid in positions}, **{m["meeting_id"]: m for m in new_meetings if m["meeting_id"] not in positions}}
    ordered = sorted(all_items.values(), key=lambda m: (m["sort_timestamp"], m["meeting_id"]), reverse=True)
    if all(m["meeting_id"] in positions for m in new_meetings):
        return {"requests": [], "ordered_meeting_ids": [m["meeting_id"] for m in ordered]}
    requests = []
    lengths = {}
    def collect_ranges(doc):
        for entry in doc.get("namedRanges", {}).values():
            for named in entry.get("namedRanges", []):
                if named.get("name", "").startswith("granola_"):
                    r = named["ranges"][0]
                    lengths[named["name"][8:]] = r["endIndex"] - r["startIndex"]
                    requests.append({"deleteNamedRange": {"namedRangeId": named["namedRangeId"], **({"tabsCriteria": {"tabIds": [tab_id]}} if tab_id else {})}})
        for tab in doc.get("tabs", []):
            collect_ranges(tab.get("documentTab", tab))
            collect_ranges({"tabs": tab.get("childTabs", [])})
    # Detach markers first so inserting at an old section boundary cannot expand them.
    collect_ranges(document)
    # Insert oldest new item first, updating all remembered UTF-16 positions.
    for item in reversed(ordered):
        mid = item["meeting_id"]
        if mid in positions:
            continue
        rank = next(i for i, m in enumerate(ordered) if m["meeting_id"] == mid)
        older = next((m["meeting_id"] for m in ordered[rank + 1:] if m["meeting_id"] in positions), None)
        if older:
            index = positions[older]
        elif positions:
            # Append after the last existing named section, before final document newline.
            body = document.get("body", {})
            if tab_id:
                def find(tabs):
                    for tab in tabs:
                        if tab.get("tabProperties", tab).get("tabId") == tab_id:
                            return tab.get("documentTab", tab).get("body", {})
                        found = find(tab.get("childTabs", []))
                        if found: return found
                    return {}
                body = find(document.get("tabs", [])) or body
            index = max(e["endIndex"] for e in body["content"]) - 1
            index += sum(utf16(section(n)[0]) for n in new_meetings if n["meeting_id"] in positions and n["meeting_id"] not in named_positions(document))
        else:
            index = 1
        text, styles, bullets = section(item)
        loc = {"index": index, **({"tabId": tab_id} if tab_id else {})}
        rng = lambda a, b: {"startIndex": a, "endIndex": b, **({"tabId": tab_id} if tab_id else {})}
        requests.append({"insertText": {"location": loc, "text": text}})
        requests.append({"updateParagraphStyle": {"range": rng(index, index + utf16(text)), "paragraphStyle": {"namedStyleType": "NORMAL_TEXT", "pageBreakBefore": False}, "fields": "namedStyleType,pageBreakBefore"}})
        for a, b, style in styles:
            if b > a:
                requests.append({"updateParagraphStyle": {"range": rng(index+a, index+b), "paragraphStyle": {"namedStyleType": style}, "fields": "namedStyleType"}})
        lengths[mid] = utf16(text)
        positions = {key: value + utf16(text) if value >= index else value for key, value in positions.items()}
        positions[mid] = index
    for i, item in enumerate(ordered):
        start = positions[item["meeting_id"]]
        requests.append({"createNamedRange": {"name": "granola_" + item["meeting_id"], "range": {"startIndex": start, "endIndex": start + lengths[item["meeting_id"]], **({"tabId": tab_id} if tab_id else {})}}})
        requests.append({"updateParagraphStyle": {"range": {"startIndex": start, "endIndex": start + utf16(item["date"] + " - " + item["source_record"]["document_title"]), **({"tabId": tab_id} if tab_id else {})}, "paragraphStyle": {"pageBreakBefore": i != 0}, "fields": "pageBreakBefore"}})
    return {"requests": requests, "ordered_meeting_ids": [m["meeting_id"] for m in ordered]}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    parse = commands.add_parser("parse")
    parse.add_argument("source")
    parse.add_argument("--out", required=True)
    parse.add_argument("--timezone", default="America/Los_Angeles")
    archive = commands.add_parser("archive")
    archive.add_argument("--meetings", required=True)
    archive.add_argument("--out", required=True)
    batch = commands.add_parser("batch")
    batch.add_argument("--new", required=True)
    batch.add_argument("--document", required=True)
    batch.add_argument("--existing", required=True)
    batch.add_argument("--tab-id")
    batch.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.command == "parse":
        meetings = read_export(args.source, args.timezone)
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        for m in meetings:
            (out / (m["meeting_id"] + ".json")).write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (out / "meetings.json").write_text(json.dumps(meetings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"meetings": len(meetings), "out": str(out), "empty_summaries": [m["meeting_id"] for m in meetings if not m["source_record"]["summary"]], "empty_transcripts": [m["meeting_id"] for m in meetings if not m["source_record"]["transcript"]]}))
    elif args.command == "archive":
        meetings = json.loads(Path(args.meetings).read_text(encoding="utf-8"))
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        for meeting in meetings:
            (out / ("granola-" + meeting["meeting_id"] + ".json")).write_text(json.dumps(transcript_payload(meeting), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"transcripts": len(meetings), "out": str(out)}))
    else:
        load = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
        result = build_batch(load(args.new), load(args.document), load(args.existing), args.tab_id)
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"requests": len(result["requests"]), "sections": len(result["ordered_meeting_ids"])}))

if __name__ == "__main__":
    main()
