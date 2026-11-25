# personal-plugin

Tejit's personal skills plugin for Claude and ChatGPT/Codex.

## Skills

| Skill | Purpose |
|---|---|
| `jira` | Create/update Onolys Jira tickets via Atlassian Rovo (current sprint, under an epic) |
| `tick` | Manage personal tasks in TickTick |
| `import-granola-meetings` | Import Granola exports into Google Drive, routed by nonprofit/Onolys/personal |
| `index-drive-folders` | Create/refresh `index.md` navigation files across a Drive folder tree |
| `answer-from-drive-indexes` | Answer questions from a Drive folder using its indexes |
| `nonprofit-context` | Context skill: nonprofit sources and where nonprofit tasks go (TickTick) |
| `onolys-context` | Context skill: Onolys sources and where Onolys tasks go (Jira) |

The two context skills hold routing rules; `jira`, `tick`, `import-granola-meetings`, `index-drive-folders` and `answer-from-drive-indexes` reference them and defer to them.

## Required connectors

Atlassian Rovo, TickTick, Granola, Google Drive / Docs / Sheets, Gmail, Google Calendar.

## Install

**Claude Code**
```
/plugin marketplace add tejitpabari99/personal-plugin
/plugin install personal-plugin@personal-plugin
```

**Claude.ai / desktop**: zip each skill folder under `plugins/personal-plugin/skills/` and upload in Settings -> Capabilities -> Skills (or add the marketplace if your org supports it).

**ChatGPT / Codex**: add the marketplace from this repo (it reads `.agents/plugins/marketplace.json`), then install `personal-plugin`:
```
codex plugin marketplace add tejitpabari99/personal-plugin
```
