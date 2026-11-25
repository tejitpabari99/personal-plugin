# Nonprofit project priority tracker

Read this only when the import plan contains a genuinely new nonprofit meeting ID.

## Canonical sheet

- Nonprofit root: `1hITV6H69P4WNLiOyTXRDZDrJhFpAUZaC`
- Spreadsheet: `1tLFT1uA2WQjt7zbYYCXcwvMQof0Z2dWT3EiP8u8pnco`
- Tab: `Project Priority`

Use the IDs, verify the parent and tab, and edit in place. The Sheet sits beside `index.txt`.

## Columns

Maintain one row per normalized `(NGO, Project)`:

| Column | Rule |
|---|---|
| Priority | User-controlled. Preserve values and row order; append a new project with the next integer unless explicitly directed otherwise. |
| NGO | Canonical nonprofit folder name. |
| Project | Match the dashboard heading. |
| Project Description | One-line current problem/work description. |
| Date Added | `YYYY-MM-DD`; set once from the eligible meeting that establishes the project. |
| Status | User-controlled except for an explicit transition in an eligible meeting. |
| Next Action | Most immediate current ask. |
| Waiting On | Person or organization blocking it; blank when unknown. |
| Meeting Notes | Full URL to that NGO's notes Doc. |
| Last Meeting | `YYYY-MM-DD`; update only when an eligible meeting discusses the project. |

Use text dates so sorting is deterministic.

## Status contract

The Status dropdown contains exactly: `To do`, `In progress`, `In review`, `Waiting`, `Upcoming`, `Done`.

Use gentle conditional colors:

- To do: soft gray
- In progress: light green
- In review: light yellow
- Waiting: the same light yellow as In review
- Upcoming: light blue
- Done: light green with darker green text

Keep the header and first three columns frozen, gridlines hidden, wrapped text, readable widths, filters enabled, and the native table range equal to the exact populated rectangle.

## Incremental rules

1. Read metadata and bounded cells before writing. Only projects created or updated from the current run's frozen `new_nonprofit_meeting_ids` may change rows.
2. Never reconstruct rows from historical meetings. Read [nonprofit-project-overrides.md](nonprofit-project-overrides.md).
3. Preserve manual Priority, row order, Status, and stronger manual descriptions unless an eligible meeting explicitly changes status or facts.
4. Add only a newly confirmed project. Do not add speculative ideas.
5. If an eligible meeting explicitly completes a project, set Done and clear completed Next Action/Waiting On. Completing one ask does not complete the project.
6. Never delete a row automatically. Use targeted batch updates and verify values, links, dropdown validation, conditional formats, and table range.
