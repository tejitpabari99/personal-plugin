---
name: "tick"
description: "Manage personal tasks in TickTick through the connected TickTick integration. Use for @Tick, creating or updating tasks by name or description, task lists, smaller subtasks, dates, recurrence, and a read-only fix command to review duplicates and cleanup. Reuse similar tasks, use only existing relevant lists and tags, and omit dates unless supplied."
---

# Tick

For nonprofit work, first load the `nonprofit-context` skill; its list/tag/section rules override the generic defaults below.

Use the connected TickTick MCP tools for personal work. Keep Jira work separate unless explicitly instructed otherwise. Follow current tool schemas; reuse authenticated access without asking for credentials.

## Discover lists, tags, and tasks

- Discover lists through list_projects and tags through list_tags at the start of the operation. Resolve actual IDs and tag names from results. Do not hardcode project IDs, list names, tag names, or a fixed classification catalog in this skill.
- Match a task to an existing user-defined list only when its subject clearly fits that list or the user explicitly selects it. Allow display emojis and case differences when resolving a named list. Put unmatched tasks in the discovered default Inbox; this represents no custom list. Never create a new list just because a task introduces a new topic.
- Apply an existing user-defined tag only when the task actually matches the tag's specific meaning or the user requests it. List membership does not imply a tag. For example, a post-specific tag applies to writing or publishing a post, not all outreach, replies, or other tasks in a networking list. If no tag fits, create with no tags.
- Do not create, rename, or delete lists or tags unless explicitly requested. Treat any one-time tag reset as account maintenance, not an action to repeat whenever the skill runs.
- Read existing tasks before creating: search with distinctive terms and synonyms, fetch candidate details, and inspect relevant lists plus Inbox. get_project_with_undone_tasks includes undated tasks; date-window tools alone are insufficient. Respect pagination and report access failures instead of treating failed search as no match.

## Create or update

1. Identify each requested task. Create one task per distinct item in a list; keep supporting requirements within the parent task unless subtasks are requested.
2. Compare existing candidates by intended action, subject, scope, and outcome. When a very similar active task exists, add new details to it instead of creating a duplicate. Preserve existing useful text, links, checklist progress, hierarchy, dates, reminders, recurrence, and unrelated fields. Do not repeat information or links already present. Distinguish separate recurring occurrences and completed work from new follow-up work. Clarify if multiple plausible matches or a completed match make intent unclear.
3. Use a clear action-oriented title and a concise, formatted description with relevant details, links, and completion criteria supported by the request. Do not invent requirements or facts. Use content for TEXT tasks and desc for CHECKLIST tasks as the API requires.
4. For new tasks, use only an existing relevant list and tags; otherwise Inbox and no tags. Do not add start dates, due dates, reminders, priority, or recurrence unless the user supplies them. Existing dates are preserved when updating without date instructions. Interpret supplied relative dates in the user's timezone; discover preferences if needed. Use all-day dates when no time is supplied. For explicitly requested recurrence, prefer TickTick's native repeatFlag/repeatFrom using a valid rule; clarify any missing date essential to scheduling rather than inventing one.
5. Accept update targets by name, description, URL, or ID. Read full current details before editing. Support title/description changes, links, completion/status changes, dates, list moves, and tags with the appropriate tools. For an update-only request with no match, report that rather than creating a task. Preserve current list/tag assignments unless classification or movement is requested or clearly part of the user's instruction; do not perform a global cleanup incidentally.
6. Support explicitly requested subtasks or checklist breakdowns into manageable actions with clear completion conditions. Use parentId for true subtasks and checklist items when requested. Resolve/reuse parents first and check existing children for duplicates. Preserve checklist IDs and completion states. Do not flatten an existing hierarchy or create unrelated extra work.
7. Verify results, inspect batch id2error responses, and retry only failed operations. After an uncertain write, look for the created task before repeating it. Never claim creation/update succeeded merely because a call returned.
8. Return clickable links for every created or updated task and relevant list, using canonical URLs returned by the integration/search. Label results Created or Updated existing and use readable task names. If a URL cannot be verified, say so rather than guessing one.

## Fix: suggestions only

Treat `fix` or `@Tick fix` as strictly read-only. Do not merge, delete, complete, edit, move, retag, reschedule, or create tasks, lists, or tags. TickTick has no epic concept; do not propose Jira-style epics.

- Discover all accessible lists and tags, then read all active tasks across the lists and Inbox, including undated tasks and children. Page fully where supported. Read completed candidates where relevant and supported; state review coverage and gaps, never imply all-history coverage if the API cannot provide it.
- Identify likely duplicates and overlapping tasks. Compare full intent and details, distinguish related work, parent/child structure, and separate recurring occurrences. Suggest a retained task and how useful notes or checklist progress could be combined, with reasons and confidence.
- Suggest clearer wording, manageable chunks for oversized tasks, redundant checklist cleanup, or moving/labeling tasks with suitable EXISTING lists/tags. Leave unmatched work in Inbox with no tags. Do not propose new lists/tags unless the user asks to design them. Do not suggest arbitrary dates.
- Present a short prioritized review with links to the affected tasks, proposed action, and rationale. Explicitly state that no changes were made.
- Apply only particular changes explicitly authorized in a later request, after reading current task state again. The word fix alone never authorizes changes.