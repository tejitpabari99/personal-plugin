---
name: "jira"
description: "Create and manage Jira tickets using Atlassian Rovo. Use when the user invokes @Jira, asks to create a Jira task or ticket, provides a list of tasks to turn into tickets, or asks to inspect or update existing Jira issues. Find similar existing tasks before creating new ones; update tickets by key, name, or description. Default to the Onolys space at onolys.atlassian.net and create new tasks in the current sprint under an epic with clear titles and formatted descriptions."
---

# Jira

For Onolys work, first load the `onolys-context` skill; its rules override the defaults below.

Use the connected Atlassian Rovo tools for all Jira reads and writes. Reuse the user's authenticated connection; never request credentials in chat.

## Defaults

- Create new tasks in the current active sprint unless the user explicitly says backlog (or another destination). Do not assign them to a future sprint by default.
- Create one separate ticket per task when the user supplies multiple tasks or a task list. Keep supporting bullets within their parent task unless the user identifies them as separate tasks. Do not merge distinct tasks or create an extra umbrella ticket unless requested.
- Prefer the Task issue type unless the user requests another type. Check project-supported issue types when necessary.
- Give every ticket a concise, action-oriented title and a useful, properly formatted description. Preserve the user's scope, links, technical details, and constraints. Do not invent requirements or facts.
- Default to https://onolys.atlassian.net and its Onolys space/project. Resolve the actual project key, cloudId, and board from live metadata; do not guess their IDs or assume the project key is ONOLYS. Reuse verified identifiers within the session. Ask only if multiple Onolys projects or boards remain plausible. Honor an explicit alternative destination.
- Leave assignee, priority, labels, dates, and estimates unspecified unless requested or required by the project. For parent selection, follow Existing epic placement below (every task must have an epic). Resolve user identities through the appropriate assignable-user operation when assigning a ticket.

## Ticket formatting

Use Markdown descriptions (contentFormat: markdown), which Rovo converts to Jira's native format. Use headings, short paragraphs, and bullets. Scale the description to the task; omit empty or irrelevant sections.

Suggested description:

## Description
Explain the requested change and relevant context.

## Requirements
- Capture the specific work and constraints supplied by the user.

## Acceptance criteria
- State observable completion criteria supported by the request, where useful.

## References
- Include supplied links or related ticket keys when available.

For bugs, include observed behavior, expected behavior, and reproduction steps only when known. Keep missing critical information explicit rather than inventing it.

## Execution

1. Parse the request and identify each ticket or requested update. A request to create tickets authorizes creation; proceed without an extra confirmation when the destination and task scope are clear. If the user asks only for a draft or list, return that without creating tickets.
2. Call getAccessibleAtlassianResources once per session, cache the selected cloudId, and pass it explicitly to subsequent site-scoped tools. Use available metadata operations through Rovo discover and executeRead to resolve projects, boards, required fields, and valid issue types as needed. Follow each tool's current schema.
3. Before creating EACH task, search the Onolys project for very similar existing tickets using Rovo semantic search and, where useful, project-scoped JQL with distinctive keywords. Search across statuses, including completed tickets, and compare candidate descriptions and scope with getJiraIssue. Match on intended work, affected component, and outcome, not title resemblance alone. If one clear very similar task exists, update that ticket with the new information instead of creating another; preserve its existing useful content and workflow state unless the user asks to change them. If several plausible matches remain, ask which ticket to update before writing. If the only match is completed and it is unclear whether this is new work or an update, clarify rather than silently reopening it. Check earlier tickets in the same batch as well. If search fails, resolve the failure rather than treating it as no match. Only if no very similar task exists, call createJiraIssue with a summary and description for that task. By default, place the new task in the current active sprint (resolve the active sprint from board metadata and verify it); omit assignToSprint and any Sprint field only when the user asked for backlog.
4. By default, ensure each new ticket is in the current active sprint (resolved from board metadata and verified). Only when the user says backlog, explicitly ensure backlog placement using transitionJiraIssue with assignToBacklog: true and the resolved boardId when needed. Backlog placement is separate from workflow status: do not assume a status named Backlog exists or transition to In Progress. Verify the operation's result and board eligibility where necessary; report any unresolved placement rather than claiming success.
5. If a create response already contains an issue key, do not create that ticket again when a subsequent placement or field update fails. Repair or retry the failed step using the existing key. After an uncertain write result, check for an existing ticket before retrying creation.
6. For existing tickets, read their current contents before updating and preserve unrelated fields. Apply only the requested edits or transitions. Do not move existing tickets to the backlog merely because this skill is invoked; the current-sprint default applies to new tasks.
7. Always return a clickable link to the relevant board and a clickable link to EVERY created or updated ticket. Resolve the board using Jira metadata and prefer its returned canonical URL; if none is returned, construct the board URL only from verified site, project key, and board ID. Never invent a board ID. Ticket links may use https://onolys.atlassian.net/browse/<verified-issue-key>. Label each result Created or Updated existing, include the key and title, and state any requested status change. For multiple tasks, use a concise list or table. State backlog placement only when verified, and identify partial failures or an unresolved board link rather than claiming success.

## Update tickets by name or description

- Accept an issue key or URL, a task name, or a description of the work. For a key or URL, read that ticket directly. Otherwise, search within the Onolys project and read likely candidates. A unique, well-supported match is sufficient to proceed; ask which ticket only when the target remains ambiguous. If no match exists, report that and ask for a more specific locator rather than creating a ticket for an update-only request.
- Support requested title/description edits, adding links, comments, field updates, and workflow status changes using the appropriate Atlassian Rovo operations. Preserve unrelated fields and existing information.
- For adding a link, add it to the description's References section unless the user specifies a comment, attachment, issue relationship, or remote link. Avoid adding the same link twice. Use supported linking operations when a relationship is requested.
- For status changes, discover and read the issue's available transitions and use the valid transition ID. A transition name may differ from its target status. If already in the requested status, report that without a redundant write. If no supported transition reaches the requested status, explain the available choices; do not guess IDs or directly overwrite status.
- Read tool results to verify the requested edits or landed status; read back when needed. Return the board link and ticket links for updates as well as creations.


## Tasks and subtasks

- Support explicitly requested tasks and subtasks, including breaking a task down into smaller subtasks. Use manageable, concrete actions with clear completion conditions to support the user's ADHD workflow. Keep each chunk focused on one outcome; do not create subtasks automatically for ordinary task requests.
- Resolve supported issue types from project metadata. Find or create the parent first, then create children using its verified key in the parent field. Search for very similar parents and inspect existing children for duplicates before creating; update clear matches instead. Do not silently reparent a ticket found elsewhere.
- Preserve existing parent status and sprint unless requested otherwise. New top-level tasks default to the current active sprint (backlog only when the user says so). Subtasks inherit parent board/sprint context and may not support independent backlog placement; do not force unsupported moves. If a parent is in a sprint but backlog-only children are requested, clarify before creation rather than moving the parent.
- Return the board link and links to the parent and EVERY created or updated child, grouped by hierarchy. Retry only failed steps if creation is partial.

## Fix command: review only

Treat `fix`, `@Jira fix`, or a request to review duplicates and suggest epic organization as a strictly read-only command. NEVER create, update, merge, delete, comment on, reparent, transition, or move tickets or epics during this command. Suggest only; fix by itself does not authorize any writes.

1. Read ALL accessible issues in the Onolys project, paging to completion. Include backlog and sprint issues, completed issues, unassigned work, epics, tasks, and subtasks. Do not restrict to the user's assigned tickets or the first page. Inspect titles, descriptions, statuses, types, parent/epic relationships, and relevant links; fetch full candidate descriptions where necessary. If a full review is blocked, state coverage and remaining gaps.
2. Identify likely duplicate groups and overlapping work by intent, scope, component, and expected outcome. Distinguish true repeats from related tasks, separate phases, parent/child relationships, and new follow-up work on completed tasks. Give linked issue keys, the reason, confidence, and a suggested ticket to retain or next step for each group.
3. Review existing epics before proposing new ones, and flag tasks with no epic and epics with no description. Suggest grouping related tasks under a suitable existing epic, or propose a new epic with a title, short purpose, and linked candidate tasks. Clearly distinguish existing and proposed epics. Avoid unrelated groupings or an epic for each small task. Preserve useful hierarchy in recommendations.
4. Provide a concise, prioritized review with the board link and links to every referenced issue. Suggest smaller chunks for oversized tasks where useful, without creating them. State explicitly that no changes were made.
5. Only a later explicit request to apply specific suggestions authorizes changes. Re-read affected issues and apply only the requested edits; resolve ambiguities before writing.


## Existing epic placement

- Before creating a new top-level task, discover existing epics in the target project and compare their titles and descriptions with the task scope. Attach the task to a clearly relevant existing epic using its verified key as parent. Honor an explicit epic choice.
- Every new top-level task MUST belong to an epic. If no existing epic clearly fits, ask the user before creating a new epic or choosing one; create an epic (title plus description) only after the user confirms, then create the task under it and tell the user the epic was created. Do not force unrelated work into an unrelated epic.
- Every epic MUST have a description (## Description: purpose and scope, using only facts supplied by the user). When creating an epic, always write one. If you encounter an existing epic with no description, mention it to the user, and add a description only when its purpose is clear from its child tasks or the user's input.
- If multiple epics plausibly fit and no clear best match exists, ask the user which epic to use before creating or choosing one. Preserve existing task hierarchy on duplicate updates unless the user requests a move.
- Subtasks belong under their task, not directly under an epic. The fix command remains read-only and may suggest potential epics or missing descriptions, but cannot create or edit them.