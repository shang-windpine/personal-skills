# Templates

Working notes, not published documentation. Terse, cited, honest about gaps.

## INDEX.md

```markdown
# Codebase Map — Index

Last session: <date> · Target: <what was investigated>

## Capability coverage

| Capability | Status | File | Notes |
|---|---|---|---|
| <e.g. Order intake> | solid | L2-order-intake.md | |
| <e.g. Payment settlement> | partial | L2-payment-settlement.md | trace done, refunds unmapped |
| <e.g. Nightly reconciliation> | unknown | — | batch job, no HTTP surface |
| <e.g. Legacy export> | — | — | suspected dead, confirm with team |

Status is one of `unknown`, `partial`, `solid`. Downgrade to `partial` when a
later finding contradicts what a file says.

## Capability × component matrix

| Capability | PostgreSQL | MongoDB | Redis | RabbitMQ |
|---|---|---|---|---|
| Order intake | orders, order_lines | — | idempotency keys | publishes order.created |
| Payment settlement | payments | payment_events | distributed lock | consumes order.created |

Fill cells only with verified usage. This table answers both "what does this
feature touch" and "who depends on this queue".

## Open questions

1. <question> — would be resolved by <file to read / runtime check / person to ask>

## Next targets

1. <capability> — <why this is highest value next>
2. <capability> — <why>
```

## L0-orientation.md

```markdown
# L0 — Orientation

## What this service does
<2-3 sentences in business terms, not technical ones>

## Modules
| Module | Responsibility | Depends on | Evidence |
|---|---|---|---|

## Entry point and startup sequence
<Ordered list of what gets deployed, in what order, with citations>

## Config
| Source | Precedence | Contents | Evidence |
|---|---|---|---|

## Conventions needed to read any file
<The minimum framework knowledge required: how handlers are registered, how
EventBus addresses are declared, how async failures propagate, where constants
live. Just enough to stop being confused — not a full component study.>

## Running locally
<Verified commands only. Mark unverified ones as untested.>

## Open questions
```

## L1-capabilities.md

```markdown
# L1 — Capability Map

Broad and shallow by design. Boundaries here are provisional.

| # | Capability | What it does (business terms) | Trigger | Owning packages | Confidence |
|---|---|---|---|---|---|
| 1 | <name> | <one sentence> | HTTP / MQ / cron / internal | `com.x.y` | high/medium/low |

## Suspected dead
| Capability / code | Why suspected dead | Confirm with |
|---|---|---|

## Boundary uncertainties
<Where it is unclear whether something is one capability or two, and what
would settle it>

## Prioritized backlog
<Ordering with reasoning, so a later session need not re-derive it>
```

## L2-\<capability\>.md

The main artifact. One per business capability.

```markdown
# L2 — <Capability>

## Business purpose
<What business need this serves and why it exists. If the "why" is not
answerable from code, record it as an open question for a teammate.>

## Trigger surface
| Trigger | Type | Location | Notes |
|---|---|---|---|
| `POST /v1/orders` | HTTP | `path:line` | |
| `order.created` | MQ consumer | `path:line` | |

## Domain model and invariants
<The entities involved, what each means in business terms, and the rules that
must always hold. Include state machines as an explicit transition table.>

| From | Event | To | Guard | Evidence |
|---|---|---|---|---|

## Business rules
<Thresholds, eligibility conditions, retry counts, calculation formulas.
Record these verbatim with citations — paraphrasing is how subtle bugs get
introduced later.>

## End-to-end trace: <one concrete operation>
Required. Every hop from ingress to every side effect.

1. `path/File.java:12` — <what happens and the decision made here>
2. `path/File.java:45` — <...>

### Side effects
| Effect | Store / destination | Conditional on | Evidence |
|---|---|---|---|

### Failure behavior
<What happens when each step fails: retried, dead-lettered, silently
swallowed, partially committed. Where partial failure leaves inconsistent
state, say so explicitly.>

## Data ownership
<Which tables, collections, and keys this capability owns versus merely reads.
Note anything it writes that another capability also writes — shared write
access is a frequent source of bugs.>

## Depends on / depended on by
| Direction | Capability | Via | Evidence |
|---|---|---|---|

## Component conventions observed
<How this capability uses each infrastructure component. Once the same
convention shows up in a second capability, promote it to a ref- file.>

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
| <abbreviation or domain word> | <plain explanation> | `path:line` |

Include internal jargon, ambiguous class-name prefixes, and status/enum codes
whose values are not self-explanatory.
```
