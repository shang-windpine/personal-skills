# Cross-Repo Stitching

How a frontend call site and a backend handler become one cited chain. The join key is **HTTP method + normalized path**.

## `ref-http-contract.md` — derive, never assume

Path normalization rules differ per deployment and are **derived on site, during each repo's L0 pass**, then recorded in the atlas's `ref-http-contract.md`. This skill deliberately ships none of them. Derive, from each side:

- **Frontend side**: the API client's base URL(s) and how they compose with per-call paths; any gateway or proxy prefix added at build/deploy time (dev-server proxy config, env vars); how path parameters are interpolated.
- **Backend side**: router mount points and sub-router prefixes; the API version scheme (e.g. a `/api/v2/…` segment on the public surface); path-parameter syntax as registered (`:id` vs `{id}` vs regex); whether trailing slashes or case matter.
- **The normalized form** the atlas uses for the join key: one canonical spelling per endpoint — strip the gateway prefix or keep it (pick once, record the choice), placeholder syntax for path params (recommend `{param}`), version segment kept verbatim.

The contract file is complete when a call site's constructed URL and a handler's registered route can each be mechanically rewritten to the same normalized string. Every stitch afterward cites it implicitly; when a stitch fails to line up, fix or extend the contract file first.

## `endpoint-index.md` — the global join table

One row per endpoint (template in [templates.md](templates.md)):

```
METHOD | normalized path | surface | frontend call site(s) | backend handler | capability | confidence
```

- **surface** is `INTERNAL` (serves the product's own UI) or `PUBLIC` (a public API offered to external developers — a business capability of its own). One normalized path can appear on both surfaces; that is two rows.
- Rows may be **half-filled**: a frontend pass adds call-site rows with an empty handler cell; a backend pass adds handler rows with empty call-site cells. The join key aligns the halves — filling the other half of an existing row is a first-class session outcome.
- Detailed per-hop chains live in the capability's L2 file; the index holds only the join row. Keep them in sync: any session that touches a chain updates both.

## The public-API module boundary (PUBLIC surface)

Products often serve their public API from a **dedicated backend module** that delegates to internal modules. Establish during `L0-backend.md` whether this product does, and record the module's name there. If so, every `PUBLIC`-surface chain must cite two backend hops at minimum: the public-API module's entry handler, and the cross-module call into the internal implementation. Where a UI-triggered and a PUBLIC-API-triggered chain converge on the same internal code, record the convergence point in the L2 chain — that shared tail is what makes the dual-trigger view cheap to maintain.

## Stitch procedures

**From a frontend call site**: extract METHOD + constructed path → normalize per `ref-http-contract.md` → look up `endpoint-index.md`. Hit: continue the chain at the cited handler. Miss: search the backend for the route registration (probes in [stack-probes.md](stack-probes.md)), add the row, continue.

**From a backend handler**: normalize its registered route → look up the index for call sites. A `PUBLIC` endpoint may legitimately have none; an `INTERNAL` endpoint with no call site after a completed frontend pass is `suspected dead` — record it in `L1-capabilities.md`, not silently.

**Dynamic paths** (URL built from variables at runtime): mark the stitch `suspected`, cite the construction site, and note what would verify it (e.g. tracing the variable's value set).
