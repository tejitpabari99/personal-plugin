---
name: "answer-from-drive-indexes"
description: "Answer questions or complete information tasks exclusively from a Google Drive folder tree, using existing index.md files when available and temporary query-specific folder indexes when they are missing. Use when a user provides a Drive folder and asks to retrieve, analyze, compare, summarize, synthesize, or draft from its contents. Delegate one routing sub-agent per unindexed folder and one answer sub-agent per question or genuinely overlapping question group, optionally cite every supported claim, leave unsupported answers blank, and report folders that need persistent indexing."
---

# Answer from Drive Indexes

If the question is about nonprofit or Onolys work, also load `nonprofit-context` / `onolys-context` for relevant sources.

Use persistent `index.md` files as preferred routing maps. For folders without one, create query-specific temporary routing maps in memory. Then answer only from the actual contents of selected source files. Follow the Google Drive skill and keep the source Drive read-only.

## Inputs

Require:

- a Google Drive folder URL or resolvable folder ID;
- one or more questions, or a task to complete from the folder's information.

Treat `references`, `citations`, `sources`, `show where this came from`, and equivalent language as a request for referenced output. Otherwise return the answer without visible citations.

## Build the hybrid routing layer first

Complete routing before launching answer agents.

### Respect terminal collections

Some indexed folders deliberately act as routing leaves even though they contain organizational subfolders. Treat a folder as a terminal collection only when the user explicitly identifies it as a leaf/boundary or its exact stable Drive ID appears below. Do not infer this from its name.

| Folder | Stable Drive ID | Boundary context |
| --- | --- | --- |
| WashU Videos | `1jAS0uSZTmHIcoUhsaXwWHMZLa8U_hZfU` | Downloaded WashU CDR training videos organized into module folders. |

For a terminal collection:

- use the boundary folder's `index.md` as the persistent routing map when it is usable;
- stop recursive index discovery at the boundary folder and do not treat its module subfolders as missing, malformed, or ambiguous index locations;
- if the boundary folder itself has no usable index, assign one routing agent to the boundary folder, allow it to inspect shallow metadata for files directly inside each immediate module folder, and create one temporary routing map for the boundary folder only;
- when an answer agent selects a module folder from the boundary map, allow it to list that module folder's direct files, select relevant files from names and metadata, and open the actual selected files for evidence;
- do not use module names, filenames, video metadata, or the boundary context as answer evidence; if an actual selected video or accompanying source cannot be read, leave dependent claims unsupported;
- do not report intentionally unindexed module folders under `Folders missing index.md`.

1. Have the coordinator recursively list folder metadata to build the in-scope folder tree. For each folder, locate exact, non-trashed `index.md` files and record the folder ID, name, observed URL, parent, and depth. Stop recursion at terminal collections under the rules above. Do not answer questions during discovery.
2. When exactly one index exists, fetch it and use its entries as the persistent routing map. If it is empty or malformed, treat it as unusable, assign one routing sub-agent, and report the issue rather than using it as evidence.
3. When no index exists, mark the folder as missing an index and assign exactly one dedicated routing sub-agent to that folder.
4. When multiple exact indexes exist, do not choose one. Treat the folder as having an ambiguous index, assign one routing sub-agent, and report the ambiguity separately.
5. Process routing agents deepest-first so a folder agent receives completed relevance summaries from its direct child folders. Run siblings in parallel and batch them when concurrency is limited.
6. If sub-agent execution is unavailable, stop and say that this skill requires agents. Do not silently inspect unindexed folders or answer in the coordinator.

Give each routing agent the folder ID and observed URL, its direct-child metadata, completed direct-child routing summaries, and all atomic questions or task components. Require it to:

- inspect only that folder's direct children;
- use names, types, timestamps, and selective shallow content reads to determine which files or child folders may be relevant to each question;
- keep reads minimal: sample only enough content to write a concise query-specific description and tags or rule an item in or out;
- mark a child folder relevant to a question whenever that child's completed routing summary contains a relevant candidate, even if the child's name is vague;
- return an in-memory `index.md`-shaped routing map with stable IDs and observed links, relevance by question ID, files sampled, unreadable items, and a concise folder summary;
- make no Drive writes and never create or upload an actual `index.md`.

The coordinator must assign each unindexed or ambiguous folder once, deduplicate routing maps by folder ID, combine temporary maps with usable persistent indexes, and propagate question relevance through every ancestor so deep candidates remain reachable. A descendant relevance overlay may add a route through a persistent parent index, but it may not become answer evidence. Temporary descriptions are routing metadata only and expire after the run.

## Grounding rules

- Treat index names, descriptions, and tags as routing metadata only. They are not evidence for an answer.
- Support every factual statement with the actual contents of one or more selected source files.
- Do not use web search, general knowledge, memory, unrelated conversation context, or unselected Drive files to fill gaps.
- Permit synthesis, reformatting, comparison, and explicit arithmetic from documented inputs. Do not add unstated premises, causal explanations, extrapolations, or recommendations that the sources do not state or directly support.
- When sources conflict, preserve the conflict and attribute each position. Do not decide which is correct without source support.
- If a source cannot be read, do not answer from its index description.
- Remove every unsupported claim before returning the result.

## Split and group the request

1. Parse the request into atomic questions or task components, preserving their original order and labels.
2. Use the completed hybrid routing layer before grouping.
3. Default to one dedicated sub-agent per atomic question.
4. Group questions into one work unit only when the hybrid routing layer identifies substantially the same candidate folders or files, or when the questions are inseparable parts of one requested output. Do not group merely to reduce agent count.
5. Spawn one sub-agent per work unit. Run independent agents in parallel and batch them when concurrency is limited.
6. If sub-agent execution is unavailable, stop and say that this skill requires agents. Do not silently answer in the coordinator.

The main agent coordinates routing agents and answer agents, validates, and merges. It must not independently answer a delegated question.

## Question-agent traversal

Give each answer agent its exact question or grouped questions, the root folder, the relevant persistent and temporary routing maps, and whether visible references were requested. Require the agent to:

1. Parse the current routing map's `Folders` and `Files` entries, including stable IDs, names, descriptions, tags, question relevance, and observed Drive links.
2. Select only entries whose routing metadata directly indicates relevance to the assigned question. Do not assume that a vaguely named or unrelated entry contains the answer.
3. For a selected folder, use its supplied persistent or temporary routing map plus any descendant relevance overlays, then repeat. Do not browse unselected children as a fallback.
4. For a selected file, open the actual file through Google Drive or the appropriate Docs, Sheets, Slides, PDF, or file-reading workflow.
5. Start with the smallest sufficient source set. If evidence remains incomplete, return to the relevant routing map and inspect the next directly relevant candidate.
6. Track visited folder IDs and file IDs to prevent loops and duplicate reads.
7. Stop a branch when its routing map contains no directly relevant entry.
8. Keep all Drive access read-only and make no source-file changes.

## Require an evidence ledger

Each question agent must build an internal ledger before drafting:

- question or component ID;
- proposed claim or output field;
- supporting source-file name, stable Drive ID, and observed URL;
- precise location when available: section, page, slide, sheet and range, row, or paragraph;
- concise support note grounded in the source text.

Require each agent to return:

- a separate answer for every assigned question or component;
- its evidence ledger;
- question IDs left unsupported;
- persistent and temporary routing paths traversed;
- source files read and unreadable files;
- confirmation that it used no external facts.

Reject a claim that has no ledger entry or whose ledger points only to a persistent or temporary index description. A ledger remains mandatory even when the user did not request visible references.

## Leave unsupported answers blank

- Preserve the user's question headings, numbering, table rows, fields, or requested structure.
- For an unsupported answer, leave the corresponding value or body empty.
- Do not write `unknown`, `not found`, `N/A`, a likely answer, or an explanation inside the answer field.
- For a partly supported narrative, include only supported sentences and omit unsupported portions without adding connective claims.
- If a selected file is unreadable, leave dependent answers blank. List the access problem separately only when the user needs to take action.

## References

When references are requested:

- cite every substantive statement next to the claim;
- link the actual source file, never an `index.md`, and include the most precise available location;
- cite every source needed for a synthesis or calculation;
- do not attach a citation to an unsupported statement;
- optionally add a deduplicated `Sources used` list after the answers.

When references are not requested, omit citations and source lists from the visible response. Still use the internal evidence ledger to audit grounding.

## Merge and return

Have the coordinator:

1. Verify that every work unit was handled by exactly one agent.
2. Audit each returned claim against its evidence ledger and delete unsupported material.
3. Keep answers in the user's original order and requested format.
4. Prevent one agent's unsupported conclusion from entering another answer.
5. Apply the requested citation mode consistently across all questions.
6. Return the answer or completed task directly, without an agent trace or file-reading log unless the user asks for one.
7. Always append `Folders missing index.md` when at least one in-scope folder lacked a persistent index. Exclude descendants intentionally covered by a terminal collection boundary. List each remaining folder name with its observed Drive link and suggest running `$index-drive-folders`. This operational notice is required even when visible answer references were not requested.
8. If any folder had multiple or malformed indexes, append a separate `Index issues` notice with its observed folder link.