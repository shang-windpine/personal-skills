---
name: learn-codebase
description: Progressively build and maintain a durable understanding of a large unfamiliar backend codebase across many sessions, organized primarily by business capability rather than by technology, with findings stored in docs/codebase-map/ as a growing knowledge base. Tuned for Java + Vert.x services backed by Redis, MongoDB, PostgreSQL, and RabbitMQ. Use when the user says they are new to a project, asks to understand the structure/architecture/business logic of a codebase, asks how a feature or request flow works, asks where a middleware is used, or asks to continue/resume onboarding on a project.
---

# Learn Codebase Progressively

Understanding a large codebase is not one document — it is many small, verified passes that accumulate. This skill defines the loop and the knowledge base that makes each session build on the last instead of restarting.

## Two Axes, One Primary

**Business capability is the primary axis.** Real work arrives as "fix order cancellation", never as "fix Redis". A map organized by capability answers the questions actually asked; a map organized by technology cannot.

**Technology components are the secondary axis, and they are a byproduct.** You learn how Redis locking works *here* by tracing a capability that uses it. So component reference notes accumulate continuously as you do capability passes — they are never a phase of their own. The only infrastructure work done up front is the minimum needed to read any file at all: config sources, Verticle deployment, EventBus conventions.

Keep a `capability × component` matrix in the index. That join is what lets you answer both "what does this feature touch" and "who depends on this queue".

## Levels

**L0 — Orientation.** One pass, kept deliberately thin. What the service does in business terms, module/build graph, entry points and startup sequence, config sources and precedence, how to run and test locally, and just enough framework convention to read arbitrary code. Output: `L0-orientation.md`.

**L1 — Capability map.** A single broad, shallow pass that discovers *what the system does* and produces the backlog for everything after. Do not go deep here; the goal is a complete inventory with rough boundaries, not correctness in detail. Output: `L1-capabilities.md`. See [domain-discovery.md](domain-discovery.md) for the signals to mine and how to prioritize.

**L2 — Capability deep dives.** The main body of work: one file per business capability. Each covers the business need it serves, its trigger surface, its domain model and invariants, its business rules and edge cases, which data stores and queues it touches and why, and its dependencies on other capabilities. **Every deep dive must include at least one end-to-end trace of a real operation** — following one concrete request from ingress to every side effect is what converts a pile of facts into a working mental model. Output: `L2-<capability>.md`.

**L3 — Incremental.** From here on, every real task ends by folding what was learned back into the map. This is what keeps it alive.

Component reference notes (`ref-redis.md`, `ref-rabbitmq.md`, …) grow during L2, not on their own schedule. Only write a dedicated reference file once the same convention has appeared in two or more capabilities — before that, the detail belongs in the capability file where it was found.

## Investigation Rules

- **Lead with the business question.** For each capability, be able to state what it does and why it exists before documenting how. If the "why" is not answerable from code, that is an `OPEN QUESTION` for a teammate, and an important one.
- **Never guess.** Anything not verified in code goes under `OPEN QUESTION` with a note on what would resolve it — a file to read, a runtime check, or a person to ask.
- **Cite everything.** Every behavioral claim carries a `path/to/File.java:123` reference. Uncited claims are the main way a knowledge base rots.
- **Read wiring, not everything.** Build files, config, deployment code, route and consumer registrations, and constants tell you more per token than business logic bodies do.
- **Business rules deserve verbatim precision.** Thresholds, state machines, retry counts, and eligibility conditions get recorded exactly, with citations. Paraphrasing these is how subtle bugs get introduced later.
- **Distinguish intent from reality.** Note where naming, comments, or docs contradict the code, and trust the code.
- **Record vocabulary.** Internal jargon, abbreviations, and status codes go in `glossary.md` as encountered. In an unfamiliar domain this unblocks more reading than architecture diagrams do.
- **Keep files small.** Cap each map file near 200 lines; split a capability into sub-capabilities when it grows past that.
- **Log suspicions separately.** Landmines (blocking calls on the event loop, missing idempotency, unbounded queries) go in `risks.md` — noted, not fixed. Fixing is a separate task.

## Core Loop

Every session, in order:

1. **Read the ledger.** Open `docs/codebase-map/INDEX.md`. If it does not exist, this is the first run — start at L0.
2. **Pick exactly one target.** Either what the user asked about, or the highest-priority capability from the ledger's `Next targets`. Never take on more than one target per session.
3. **Investigate with evidence.** Delegate breadth to parallel `code-explorer` subagents; do the synthesis yourself.
4. **Write one artifact.** Create or update one capability file, append any newly generalized component conventions to their reference files, then update `INDEX.md`.
5. **Close the loop.** Report what is now understood, what remains open, and the suggested next target.

## Knowledge Base Layout

```
docs/codebase-map/
├── INDEX.md                    # Ledger: capability coverage, capability × component matrix,
│                               #   open questions, next targets
├── L0-orientation.md
├── L1-capabilities.md          # Capability inventory and boundaries
├── L2-<capability>.md          # One per business capability — the main body of work
├── ref-<component>.md          # Cross-cutting conventions, accumulated during L2
├── glossary.md                 # Domain terms and internal jargon
└── risks.md                    # Suspected problems, deliberately not fixed
```

Also add a short pointer in the repo's `AGENTS.md` so future sessions load this context automatically:

```markdown
## Codebase knowledge base
Accumulated notes live in `docs/codebase-map/`, organized by business
capability. Read `INDEX.md` first for coverage status and open questions
before exploring from scratch.
```

If the repo is shared and the notes should stay private, put them in a gitignored path instead and keep the `AGENTS.md` pointer accurate.

## Using Subagents

Breadth-first fact gathering parallelizes well; synthesis does not.

- For L1, launch several `code-explorer` subagents at once over independent slices — one per top-level package or route group — and have each report the capabilities it can identify.
- For L2, use subagents for the mechanical parts of one capability (find all callers, enumerate all persistence writes) while you keep the business reasoning yourself.
- Give each subagent concrete file globs and symbol names, since subagents do not see the conversation. Require `path:line` citations and an explicit statement of what could not be found.
- Use `system-documentation-architect` only when the user wants a polished document for others to read; map files themselves stay terse working notes.

## Session Report Format

End every session with this, and nothing longer:

```markdown
**Understood this session:** <2-4 sentences of business substance, not a file list>
**Written to:** <map file(s) touched>
**Still open:** <the 1-3 most important unknowns>
**Suggested next:** <one target, with why it is next>
```

## When NOT to Use This Skill

Skip the full loop for ordinary feature work, bug fixes, and code review. In those cases just read `INDEX.md` for context, do the task, and fold anything newly learned into the map at the end (L3). Do not start a documentation pass in the middle of someone's unrelated task.

## Additional Resources

- Finding and prioritizing business capabilities in an undocumented codebase: [domain-discovery.md](domain-discovery.md)
- Technology-specific search patterns for Vert.x, Redis, MongoDB, PostgreSQL, and RabbitMQ: [stack-probes.md](stack-probes.md)
- Templates for `INDEX.md` and each map file type: [templates.md](templates.md)
