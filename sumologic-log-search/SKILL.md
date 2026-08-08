---
name: sumologic-log-search
description: >-
  Runs readonly Sumo Logic log searches via the Search Job API using a local
  script and credentials file. Use when the user asks to query Sumo/SumoLogic
  logs, investigate errors from Sumo, search _sourceCategory, or fetch recent
  log lines without MCP.
---

# Sumo Logic Log Search (Readonly API)

Query Sumo Logic with the bundled script. Do **not** configure or use Sumo MCP.

Paths below are relative to this skill directory (the folder that contains
`SKILL.md`). Resolve them from where this skill is installed — for example
`~/.agents/skills/sumologic-log-search`, `~/.claude/skills/sumologic-log-search`,
`~/.codex/skills/sumologic-log-search`, `~/.cursor/skills/sumologic-log-search`,
or a project-local `.agents/skills/sumologic-log-search`.

## Credentials (never print)

Path: `~/.config/sumologic/credentials` (mode `600`)

```bash
# One-time setup on the machine that will run queries (cwd = this skill directory)
mkdir -p ~/.config/sumologic
cp credentials.example ~/.config/sumologic/credentials
chmod 600 ~/.config/sumologic/credentials
# Edit and fill SUMO_ACCESS_ID, SUMO_ACCESS_KEY, SUMO_API_ENDPOINT
```

- Prefer Personal Access Key with **Run Log Search** only (or company minimum).
- `SUMO_API_ENDPOINT` must match the deployment (from login host `service.X.sumologic.com` → `https://api.X.sumologic.com`; US1 → `https://api.sumologic.com`).
- Never echo Access ID/Key, never paste credentials into chat, never commit the credentials file.
- Env vars `SUMO_ACCESS_ID` / `SUMO_ACCESS_KEY` / `SUMO_API_ENDPOINT` override the file if set.

## How to search

Run from this skill directory (or pass an absolute path to the script):

```bash
python3 scripts/sumo_search.py \
  --query '_sourceCategory=your/category error | limit 50' \
  --from '-15m' \
  --to 'now' \
  --limit 50
```

Useful flags:

| Flag | Meaning |
|------|---------|
| `--from` / `--to` | `-15m`, `-1h`, `-1d`, `now`, epoch ms, or ISO-8601 |
| `--limit` | Max rows returned (1–1000, default 50) |
| `--timezone` | Default `UTC` |
| `--raw` | Full message maps instead of compacted fields |
| `--keep-job` | Skip deleting the search job after fetch |

Script behavior: create job → poll until done → fetch messages or aggregate records → delete job. Cookies are handled automatically.

## Agent rules

1. Use this skill for Sumo log questions; do not invent MCP setup.
2. Translate the user ask into a Sumo query; if `_sourceCategory` / service name is unknown, ask once.
3. Default window: last 15 minutes unless the user specifies otherwise.
4. Keep `--limit` small (≤100) unless the user needs more.
5. Summarize findings in Chinese (errors, counts, sample `_raw` lines). Cite query + time range.
6. Readonly only: search logs. Do not manage collectors, users, dashboards, or keys.
7. If credentials are missing, tell the user to create `~/.config/sumologic/credentials` from this skill's `credentials.example` — do not ask them to paste secrets into chat.
8. On HTTP 403, note Search Job API may require Enterprise/Trial entitlements.

## Install / other machines

Copy or install this whole skill folder into the target harness's skills path, set up credentials once, then invoke the skill or run `scripts/sumo_search.py`. No MCP required.
