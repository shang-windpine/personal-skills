# Domain Discovery

How to find the business capabilities of an undocumented service, and which to map first.

## What Counts as a Capability

A capability is something the business would recognize as a thing the system does: "accept an order", "settle a payment", "reconcile inventory nightly". It is not a technical layer, not a class, and not a table.

Two traps to avoid:

- **Layered packaging masquerading as structure.** If top-level packages are `controller` / `service` / `repository` / `dto`, the package tree tells you nothing about the domain and you must use the other signals below. If they are `order` / `billing` / `inventory`, the tree is your first draft of the capability list — but verify it, since package names drift from reality.
- **Class names are not domain concepts.** A `ProcessorManager` may implement three unrelated capabilities, and one capability may be spread across a dozen classes. Group by business outcome, not by file.

## Signals, Roughly in Order of Value

**1. The external API surface.** Every route registration, grouped by path prefix, is close to a literal capability list — it is what the outside world is allowed to ask for. Find them via the router registrations in [stack-probes.md](stack-probes.md), or from an OpenAPI spec if one exists.

**2. Message and event names.** MQ exchange/queue names and EventBus addresses are frequently named after business events (`order.created`, `payment.settled`, `shipment.dispatched`). This is the highest-density source of domain vocabulary in the whole repo, and it also reveals capabilities that have no HTTP surface.

**3. Scheduled and batch work.** Cron entries, timers, `setPeriodic`, scheduler configs. These are entire capabilities with no request-driven entry point, and they are the single most commonly missed category — a newcomer can work for months without discovering a nightly job exists.

**4. The persistent data model.** Cluster PostgreSQL tables by foreign-key relationships; each cluster usually corresponds to one aggregate and thus one capability. Do the same with MongoDB collection names. The entities that own the most relationships are the core of the domain.

**5. Migration history in chronological order.** This shows how the domain evolved: what the system originally did, what was bolted on later, and what got abandoned. Recent migrations point at where active development is happening.

**6. Status and state enums.** Any `enum` of statuses encodes a lifecycle, and lifecycles are capabilities. An `OrderStatus` with eight values implies eight transitions, each of which is a business rule somewhere.

**7. Git churn.** `git log --format= --name-only --since=1.year | sort | uniq -c | sort -rn` over directories reveals what the team actually works on. High-churn areas are both where you will be assigned and where the knowledge is most valuable. Also useful: files that repeatedly change *together* likely belong to one capability, even when they live in different packages.

**8. Test names.** `@DisplayName` values and descriptive test method names often state business rules in plain language more clearly than any comment in production code.

**9. Feature flags and config toggles.** Reveal optional, experimental, or per-tenant capability variations that reading code alone would present as unconditional.

**10. Non-code sources.** README, wiki links in comments, the ticket tracker, Postman collections, and commit message references to ticket IDs. Weak evidence for how things work, strong evidence for what things are *called* internally.

## Detecting Dead Capabilities

Newcomers lose enormous time carefully reading code that no longer runs. While building the inventory, actively mark:

- Routes registered but not reachable, or behind a permanently-off flag
- MQ consumers on queues nothing publishes to, and publishers to queues nothing consumes
- `@Deprecated` annotations, and classes whose last meaningful commit is years old
- Tables and collections with no writes in the current code

Mark these `suspected dead` in the inventory rather than deleting them from it, and confirm with a teammate before trusting the judgment. Knowing what to *not* read is as valuable as knowing what to read.

## Boundary Calls

When unsure whether two things are one capability or two:

**Probably one** if they share an aggregate root, are written in the same transaction, or consistently change together in git history.

**Probably two** if they have separate entry points, separate data ownership, and communicate only through events or queues.

When still ambiguous, prefer the coarser grouping. Splitting a capability file later is cheap; a map fragmented into thirty tiny files is unusable.

## Prioritizing the Backlog

Map in this order:

1. **Whatever you have been assigned.** Immediate need beats completeness, always.
2. **The money path.** The one or two capabilities without which the product does not exist. Everything else is easier to understand once this is solid, because it establishes the domain's core vocabulary and invariants.
3. **High fan-in capabilities.** Ones many others depend on. Understanding these pays off repeatedly.
4. **High-churn areas.** Where the team is actively working, so where you will be next.

Defer: admin and internal tooling, one-off data migrations, and anything marked suspected dead.

Record the ordering and the reasoning in the ledger's `Next targets`, so a later session does not have to re-derive it.
