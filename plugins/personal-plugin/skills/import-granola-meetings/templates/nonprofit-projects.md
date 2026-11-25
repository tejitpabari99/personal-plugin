# Nonprofit project dashboard

Read this only when the import plan contains a genuinely new nonprofit meeting ID.

## Eligibility

Compute the global archive diff first and freeze `new_nonprofit_meeting_ids` before writes. A meeting is eligible only when its Granola ID was absent from every ledger, transcript file, and summary marker at the start of the run.

- Create or update projects only from eligible IDs.
- Never rescan older meeting summaries, transcripts, Docs, ledgers, repaired artifacts, or skipped records to generate projects.
- A backfilled or partially recovered historical meeting is not eligible.
- A rerun of the same export makes no project changes.
- Read [nonprofit-project-overrides.md](nonprofit-project-overrides.md) before interpreting an eligible meeting.

## Document structure

The affected nonprofit's meeting-notes Doc may contain one dashboard at the top, wrapped in the exact named range `granola_projects`:

```text
Projects                         [TITLE]

<Project name>                   [HEADING_1]
Problem                          [HEADING_2]
<one concise current problem paragraph>
Asks                             [HEADING_2]
• <specific current ask>
Updates                          [HEADING_2]
<user-maintained content, possibly blank>
```

Repeat the project block for each confirmed project. Keep the first dated meeting section on a new page after the dashboard. If an organization has no confirmed projects, omit the dashboard and `granola_projects` range entirely; retain its meeting notes unchanged.

## Reconciliation

1. Read the current Doc, named ranges, and revision ID.
2. Match projects by normalized organization plus project name. Merge semantic matches; do not duplicate them.
3. A concrete workstream must be clearly confirmed in an eligible meeting before creating a project. A discussion topic, possible idea, or general capability is not enough.
4. Keep Problem current and concise. Keep Asks limited to specific open requests or actions. If an eligible meeting explicitly completes or changes an ask, remove or replace it; never infer completion from silence.
5. The user owns Updates. Preserve its content and formatting verbatim and never write into it.
6. Preserve all original Granola meeting summaries, markers, page breaks, and unrelated content. Use revision guards and targeted edits.
7. A completed project may remain with no asks. Delete a project only when the user explicitly asks.

## Verify

- Only eligible IDs influenced the dashboard.
- Exactly one `Projects` title and `granola_projects` range exist when projects exist; neither exists when none do.
- Every project has one Problem, Asks, and Updates heading.
- User-authored Updates and original meeting summaries are unchanged.
- The first dated meeting heading starts a new page when a dashboard exists.
