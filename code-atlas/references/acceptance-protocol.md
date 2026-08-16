# Acceptance Protocol

How a deployment of this skill proves its atlas works. The concrete use cases are deployment-specific and live in the KB as `docs/codebase-map/acceptance.md` (pre-placed, or written in a session with the owner); this file defines how to select them and what passing means. If the KB has no `acceptance.md`, nothing here applies.

## Selecting acceptance use cases

Pick **2–3 representative use cases** that the atlas must trace end-to-end. Selection criteria:

- **Coverage**: together they should touch the major infrastructure classes (DB, cache, MQ), and at least one should involve the product's public API surface if it has one. A use case whose UI and public-API triggers share a backend path is worth double: trace it **dual-trigger** (both legs joining at the same METHOD + normalized path), which also exercises the stitching convention and the `endpoint-index.md` surface column.
- **Representativeness**: common real support/feature-work scenarios, not exotic corners.
- **Bounded scope**: where a use case has an expensive tail (e.g. a leg delegating to an external engine), set the acceptance line at the tractable core and mark the tail a stretch goal — a stretch trace terminating at the external-system client/config boundary counts as complete, and not tracing it does not fail acceptance.

Record in `acceptance.md`: each use case with its trigger label(s), expected side-effect classes, any stretch-goal boundaries, and known coverage caveats (e.g. "none of these guarantees a cache hop — if all traces show zero cache side effects, record the gap as an open question, not a failure").

## Pass bar per trace

- **Main chain** (UI entry → frontend call site → endpoint → backend handler, or the trigger-appropriate equivalent): every hop `verified` with a `path:line` citation. Any broken hop fails that use case.
- **Side effects** (tables/collections, cache key patterns, MQ exchanges/queues): concrete names required. Individual side effects may be `suspected` but must cite the evidence location.

## Two-stage protocol

**Stage 1 — delivery gate (mechanical, at build time).** After all acceptance traces exist, self-check every main-chain hop: the cited `path:line` exists, the symbol there matches the chain's description of the hop, the hop is marked `verified`. All use cases passing = the atlas is accepted for handoff; record the result in `INDEX.md`. No human judging step — this protocol is designed for an owner who is new to the codebase and cannot referee traces from prior knowledge.

**Stage 2 — correction loop (in-use, non-blocking).** The owner reads traces during real work and reports errors as found; fix them through the QUERY workflow's backfill discipline. Quality signal, not a gate.
