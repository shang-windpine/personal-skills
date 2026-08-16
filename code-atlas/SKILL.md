---
name: code-atlas
description: Build and query a full-stack business↔code atlas across a product's frontend and backend repos, stored in a shared knowledge base. Use when starting or continuing an atlas mapping session, when new to either repo, when asked to trace a use case / feature / user action to code (UI entry → frontend call site → endpoint → backend handler → side effects), when asked which endpoint, handler, table, collection, cache key, or queue a feature touches, or where a user-visible string leads in code.
---

# Code Atlas

For a product split across **two separate repos** — a frontend (stack unknown until its L0 pass discovers it) and a backend (probes here are tuned for Java + Vert.x with Redis, MongoDB, PostgreSQL, RabbitMQ; adapt them on site if the stack differs). The atlas is one shared knowledge base that joins the repos, built from many small, verified passes that accumulate across sessions.

This skill has two workflows. **BUILD** grows the atlas one target per session. **QUERY** answers "trace this use case to code" from the atlas — and every query is also a build: gaps found while answering are traced live and backfilled, so every question leaves the map better ("query-as-mapping").

## Locate the knowledge base

The KB lives in a **shared folder next to the two repo checkouts, never inside either repo**. At session start, find the workspace folder containing `docs/codebase-map/INDEX.md` and treat it as the atlas root.

If no `INDEX.md` exists anywhere in the workspace, this is the first run:

1. Create `docs/codebase-map/` inside the non-repo shared folder, unless seed files were pre-placed there (a deployment may drop in a pre-researched `L1-capabilities.md`, `glossary.md`, and `acceptance.md`). Treat any pre-placed rows as **unverified seeds** — the first sessions confirm, correct, or delete them rather than trusting them.
2. Create `INDEX.md` from the template in [references/templates.md](references/templates.md).

## Chain model

Every mapped flow is **trigger → processing chain → side effects**. The UI hop is an optional prefix, present only for browser-originated flows.

**Every chain carries a trigger label, prominently displayed** (first thing in the trace heading):

| Label | Meaning |
|---|---|
| `UI` | browser-originated HTTP call |
| `PUBLIC-API` | external developer call on the product's public API surface |
| `MQ` | message-queue consumer |
| `CRON` | scheduled / batch job |
| `WEBHOOK` | inbound callback from an external system |
| `INTERNAL` | service-internal trigger (e.g. EventBus) |

**Every hop carries a confidence label**: `verified` (cited `path/to/File.ext:123`) or `suspected` (inferred — state from what: naming, structure, config). A chain legitimately terminates at a data store, an emitted event, or an **outbound call to an external system** (a search engine, a third-party service) — cite the client/config boundary and stop there.

Hops are tagged with their repo: `[FE]` or `[BE]`.

## Levels

- **L0 — per repo, one pass each, deliberately thin.** `L0-backend.md`: modules, deployment topology, internal messaging conventions, config sources — the minimum to read any backend file. `L0-frontend.md`: build system, routing mechanism, API client layer location, i18n mechanism, permission/feature-flag gating — the minimum to read any frontend file, discovered without assuming any framework (see [references/frontend-discovery.md](references/frontend-discovery.md)). Each repo's L0 also derives its half of the HTTP normalization rules into `ref-http-contract.md` (see [references/stitching.md](references/stitching.md)).
- **L1 — one unified capability map, atlas-wide.** A single broad, shallow inventory spanning both repos; business questions never split by tier, so neither does the map. Backend signals: [references/domain-discovery.md](references/domain-discovery.md). Frontend signals: [references/frontend-discovery.md](references/frontend-discovery.md). Starts from any pre-placed seed and refines it.
- **L2 — capability deep dives, capability-first and full-stack.** One file per capability covering both repos, hops repo-tagged. **Every deep dive includes at least one end-to-end trace** with trigger label and per-hop confidence. A session working in one repo fills only its hops; the endpoint join key aligns the halves later.
- **L3 — incremental.** Every real task ends by folding what was learned back into the map.

Component reference notes (`ref-redis.md`, `ref-rabbitmq.md`, …) grow during L2; write a dedicated file only once the same convention has appeared in two or more capabilities.

## Cross-repo stitching

Frontend call sites and backend handlers join on **HTTP method + normalized path**. Normalization rules are derived on site during each L0 and recorded in `ref-http-contract.md` — this skill deliberately ships none. `endpoint-index.md` is the global reverse-lookup table, one row per endpoint, with a `surface` column (`INTERNAL` / `PUBLIC`) because a public API offered to external developers is a business capability of its own. If the public surface is served by a dedicated backend module, `PUBLIC` chains must cite that module's entry handler and the cross-module call into the internal implementation; record the module's name in `L0-backend.md` when discovered. Full convention: [references/stitching.md](references/stitching.md).

## BUILD workflow (every mapping session, in order)

1. **Read the ledger.** Open `INDEX.md` (or run first-run setup above).
2. **Pick exactly one target** — what the user asked about, or the top of the ledger's `Next targets`. If the KB defines acceptance use cases (`acceptance.md`), they outrank everything else in `Next targets` until they pass (see [references/acceptance-protocol.md](references/acceptance-protocol.md)).
3. **Investigate with evidence.** Delegate breadth to parallel explore subagents; do the synthesis yourself.
4. **Write one artifact.** Create or update one capability file (or L0/L1), append newly generalized conventions to `ref-*` files, keep `endpoint-index.md` and `ui-text-index.md` rows in sync with any chain touched, then update `INDEX.md`.
5. **Close the loop.** Report using the session report format below.

## QUERY workflow (trace a use case)

1. **Translate vocabulary.** Look the use case's words up in `glossary.md` and `ui-text-index.md` to locate the owning capability.
2. **Emit the chain from the atlas.** Open the capability's L2 and present the full chain: trigger label first, then every hop with repo tag, citation, and confidence.
3. **On a gap** (missing capability, missing hops — the normal case early on): run a **bounded live trace** now — a mini-L2 pass scoped to just this chain — answer the user, then backfill the result into the atlas per the BUILD artifact rules (L2 file, `endpoint-index.md`, `ui-text-index.md`, `INDEX.md`).

Answer only from citations — atlas rows or code just read — never from memory of "how these apps usually work".

## Investigation rules

- **Lead with the business question.** State what a capability does and why it exists before documenting how. A "why" not answerable from code is an `OPEN QUESTION` for a teammate.
- **Never guess.** Anything unverified goes under `OPEN QUESTION` with what would resolve it, or into a hop marked `suspected` with its inference source.
- **Cite everything.** Every behavioral claim carries `path:line`. Uncited claims are how a knowledge base rots.
- **Read wiring, not everything.** Build files, config, route/consumer registrations, and constants yield more per token than business-logic bodies.
- **Business rules verbatim.** Thresholds, state machines, retry counts, eligibility conditions recorded exactly, with citations.
- **Distinguish intent from reality.** Where naming, comments, or docs contradict the code, trust the code and note the contradiction.
- **Record vocabulary.** Internal jargon, entity type names, status codes go in `glossary.md` as encountered; user-visible strings go in `ui-text-index.md`.
- **Keep files small.** Cap map files near 200 lines; split capabilities that outgrow it.
- **Log suspicions separately.** Landmines go in `risks.md` — noted, not fixed.

## Knowledge base layout

```
<shared-folder>/docs/codebase-map/
├── INDEX.md               # Ledger: coverage, capability × component matrix, open questions, next targets
├── L0-backend.md
├── L0-frontend.md
├── L1-capabilities.md     # Unified capability inventory (may start from a pre-placed seed)
├── L2-<capability>.md     # One per capability, full-stack, repo-tagged hops
├── endpoint-index.md      # Global METHOD+path join table, INTERNAL/PUBLIC surface
├── ui-text-index.md       # User-visible string → component/page → capability
├── ref-http-contract.md   # On-site-derived path normalization rules
├── ref-<component>.md     # Cross-cutting conventions (Redis, RabbitMQ, …)
├── glossary.md            # Domain terms and internal jargon
├── acceptance.md          # Optional, pre-placed: acceptance use cases for this deployment
└── risks.md               # Suspected problems, deliberately not fixed
```

If repo policy allows, add a one-line pointer to the atlas folder in each repo's `AGENTS.md`; otherwise rely on this skill's triggers.

## Using subagents

Breadth-first fact gathering parallelizes; synthesis does not. For L1, launch parallel explorers over independent slices (per top-level package, route group, or page directory). For L2, use subagents for mechanical enumeration (all callers, all persistence writes, all call sites of an endpoint) and keep the business reasoning yourself. Give each subagent concrete globs and symbol names, require `path:line` citations and an explicit statement of what could not be found.

## Session report format

End every session with this, and nothing longer:

```markdown
**Understood this session:** <2-4 sentences of business substance, not a file list>
**Written to:** <map file(s) touched>
**Still open:** <the 1-3 most important unknowns>
**Suggested next:** <one target, with why it is next>
```

## Acceptance

If the KB contains an `acceptance.md`, the atlas is accepted for handoff once its use cases pass the mechanical self-check defined in [references/acceptance-protocol.md](references/acceptance-protocol.md). Until then, treat them as the standing build backlog.

## Additional resources

- Frontend capability discovery and `ui-text-index.md`: [references/frontend-discovery.md](references/frontend-discovery.md)
- Backend capability discovery signals: [references/domain-discovery.md](references/domain-discovery.md)
- Stitching convention, `ref-http-contract.md`, `endpoint-index.md` schema: [references/stitching.md](references/stitching.md)
- Search probes per technology (backend stack + stack-agnostic frontend): [references/stack-probes.md](references/stack-probes.md)
- Templates for every map file: [references/templates.md](references/templates.md)
- Acceptance protocol and use-case selection criteria: [references/acceptance-protocol.md](references/acceptance-protocol.md)
