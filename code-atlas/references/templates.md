# Templates

Working notes, not published documentation. Terse, cited, honest about gaps.

## INDEX.md

```markdown
# Code Atlas — Index

Last session: <date> · Target: <what was investigated>
Acceptance (if acceptance.md defined): <use case> <status> · …

## Capability coverage

| Capability | FE | BE | File | Notes |
|---|---|---|---|---|
| <e.g. Order intake> | solid | partial | L2-order-intake.md | BE trace done, FE dialog unmapped |
| <e.g. Product search> | unknown | unknown | — | acceptance use case |

Per-repo status is one of `unknown`, `partial`, `solid`, `n/a` (capability has no
code in that repo). Downgrade to `partial` when a later finding contradicts a file.

## Capability × component matrix

| Capability | PostgreSQL | MongoDB | Redis | RabbitMQ | External |
|---|---|---|---|---|---|
| <name> | <tables> | <collections> | <key patterns> | <exchanges/queues> | <e.g. ES chem search> |

Fill cells only with verified usage. This table answers both "what does this
feature touch" and "who depends on this queue".

## Open questions

1. <question> — would be resolved by <file to read / runtime check / person to ask>

## Next targets

1. <capability> — <why this is highest value next>
```

## L0-backend.md

```markdown
# L0 — Backend Orientation

## What this service does
<2-3 sentences in business terms, not technical ones>

## Modules
| Module | Responsibility | Depends on | Evidence |
|---|---|---|---|
| <public-api module, if present> | public API surface | <...> | <path> |

## Entry point and startup sequence
<Ordered list of what gets deployed, in what order, with citations>

## Config
| Source | Precedence | Contents | Evidence |
|---|---|---|---|

## Conventions needed to read any file
<The minimum framework knowledge required: how handlers are registered, how
EventBus addresses are declared, how async failures propagate, where constants
live. Just enough to stop being confused — not a full component study.>

## HTTP contract inputs
<Router mount points, version scheme, path-param syntax as registered —
feed these into ref-http-contract.md>

## Running locally
<Verified commands only. Mark unverified ones as untested.>

## Open questions
```

## L0-frontend.md

```markdown
# L0 — Frontend Orientation

## What this app does
<2-3 sentences in business terms>

## Stack (discovered)
| Mechanism | What it is | Where it lives | Evidence |
|---|---|---|---|
| Build system | | | |
| Routing | <config-based / file-based / manual> | | |
| API client layer | | | |
| i18n | <catalog / hardcoded strings> | | |
| Permission / feature gating | | | |

## Route inventory location
<Where the complete route list can be enumerated from, with the command/glob used>

## HTTP contract inputs
<API client base URLs, proxy/gateway prefixes, path interpolation style —
feed these into ref-http-contract.md>

## Running locally
<Verified commands only. Mark unverified ones as untested.>

## Open questions
```

## L1-capabilities.md

```markdown
# L1 — Capability Map (unified, atlas-wide)

Broad and shallow by design. Boundaries here are provisional. Rows marked
`seed` came from public product research and are unverified from code.

| # | Capability | What it does (business terms) | Triggers | FE owning area | BE owning packages | Confidence |
|---|---|---|---|---|---|---|
| 1 | <name> | <one sentence> | UI / PUBLIC-API / MQ / CRON / WEBHOOK / INTERNAL | <route prefix / page dir> | `com.x.y` | seed / low / medium / high |

## Suspected dead
| Capability / code | Why suspected dead | Confirm with |
|---|---|---|

## Boundary uncertainties
<Where it is unclear whether something is one capability or two, and what
would settle it>

## Prioritized backlog
<Ordering with reasoning, so a later session need not re-derive it.
Acceptance use cases stay on top until they pass.>
```

## L2-\<capability\>.md

The main artifact. One per business capability, covering both repos.

```markdown
# L2 — <Capability>

## Business purpose
<What business need this serves and why it exists. If the "why" is not
answerable from code, record it as an open question for a teammate.>

## Trigger surface
| Trigger | Label | Location | Notes |
|---|---|---|---|
| Create button on orders page | `UI` | `[FE] path:line` | |
| `POST /orders` | `PUBLIC-API` | `[BE] <public-api module> path:line` | |
| `order.created` consumer | `MQ` | `[BE] path:line` | |

## Domain model and invariants
<The entities involved, what each means in business terms, and the rules that
must always hold. Include state machines as an explicit transition table.>

| From | Event | To | Guard | Evidence |
|---|---|---|---|---|

## Business rules
<Thresholds, eligibility conditions, retry counts, calculation formulas.
Record these verbatim with citations — paraphrasing is how subtle bugs get
introduced later.>

## Trace: `UI` — <one concrete operation>
Required: at least one end-to-end trace per capability. Trigger label in the
heading. Every hop repo-tagged, cited, confidence-marked.

1. `[FE] path/Component.ext:12` — verified — <UI entry: what the user does>
2. `[FE] path/apiClient.ext:45` — verified — <call site: METHOD + path as constructed>
3. `[BE] path/Handler.java:30` — verified — <endpoint handler; join key METHOD + normalized path>
4. `[BE] path/Service.java:88` — verified — <the decision made here>

### Side effects
| Effect | Store / destination | Concrete name | Conditional on | Confidence + evidence |
|---|---|---|---|---|
| insert | MongoDB | `<collection>` | — | verified `path:line` |
| publish | RabbitMQ | `<exchange> / <routing key>` | <condition> | suspected — <evidence> |

### Failure behavior
<What happens when each step fails: retried, dead-lettered, silently
swallowed, partially committed. Where partial failure leaves inconsistent
state, say so explicitly.>

## Trace: `PUBLIC-API` — <operation> (if this capability has a public surface)
<Same format. Must cite the public-API module's entry handler and the
cross-module hop. Where this chain converges with the UI chain, cite the
convergence point instead of repeating the shared tail.>

## Data ownership
<Which tables, collections, and keys this capability owns versus merely reads.
Note anything it writes that another capability also writes.>

## Depends on / depended on by
| Direction | Capability | Via | Evidence |
|---|---|---|---|

## Component conventions observed
<How this capability uses each infrastructure component. Once the same
convention shows up in a second capability, promote it to a ref- file.>

## Open questions
```

## endpoint-index.md

```markdown
# Endpoint Index

Global join table. One row per METHOD + normalized path + surface. Normalization
rules: see ref-http-contract.md. Half-filled rows are expected — the other half
arrives when the other repo's pass reaches it.

| METHOD | Normalized path | Surface | Frontend call site(s) | Backend handler | Capability | Confidence |
|---|---|---|---|---|---|---|
| POST | `/api/v2/orders/search` | PUBLIC | — | `[BE] path:line` | Product search | verified |
| POST | `<internal search path>` | INTERNAL | `[FE] path:line` | `[BE] path:line` | Product search | verified |
```

## ui-text-index.md

```markdown
# UI Text Index

Query entry point: user vocabulary → code. One row per user-visible string
encountered during any pass. i18n key if the catalog has one, else the literal.

| String / i18n key | Rendered by | Capability | Evidence |
|---|---|---|---|
| `order.cancel.confirm` ("Cancel this order?") | `[FE] path/Component.ext` | Order lifecycle | `path:line` |
```

## ref-http-contract.md

```markdown
# Reference — HTTP Contract

Derived on site during L0 passes. The join key for every stitch: a call site's
constructed URL and a handler's registered route must both rewrite mechanically
to the same normalized string using only the rules below.

## Normalized form
<Canonical spelling: prefix kept/stripped, `{param}` placeholders, version
segment handling, trailing slash / case rules>

## Frontend → normalized
| Rule | Example before → after | Evidence |
|---|---|---|
| <base URL composition, proxy prefix, interpolation> | | |

## Backend → normalized
| Rule | Example before → after | Evidence |
|---|---|---|
| <mount points, sub-routers, path-param syntax> | | |

## Surfaces
<How PUBLIC (the public-API module) and INTERNAL routes are told apart:
module, prefix, auth handler — with evidence>

## Open questions
```

## ref-\<component\>.md

Written only after a convention has appeared in two or more capabilities.

```markdown
# Reference — <Component>

## Role in this system
<Which of the several possible roles it actually plays here>

## Wiring
<Where configured and initialized, with citations>

## Inventory
<EventBus addresses, Redis key patterns, Mongo collections, PG tables, or MQ
exchanges/queues. Include which capability reads and which writes each.>

## Conventions and gotchas
<Patterns a newcomer would get wrong>

## Used by
| Capability | How | Evidence |
|---|---|---|
```

## risks.md

```markdown
# Risks

Suspected problems found while mapping. Recorded, deliberately not fixed.

| # | Risk | Location | Capability | Why it matters | Confidence |
|---|---|---|---|---|---|
| 1 | <e.g. blocking JDBC call on event loop> | `path:line` | <which> | <impact> | high/medium/low |
```

## glossary.md

```markdown
# Glossary

| Term | Meaning | First seen |
|---|---|---|
| <abbreviation or domain word> | <plain explanation> | `path:line` (or `seed` for rows from public research) |

Include internal jargon, entity type names, ambiguous class-name prefixes, and
status/enum codes whose values are not self-explanatory.
```
