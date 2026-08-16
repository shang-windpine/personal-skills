# Frontend Discovery

How to inventory business capabilities from a frontend codebase whose stack is unknown, and how to build the artifacts only the frontend can provide. Backend counterpart: [domain-discovery.md](domain-discovery.md).

## Discover before probing

The skill ships no framework assumptions. The first act of `L0-frontend.md` is to identify the mechanisms, then probe them — never the reverse. For each row below, record in L0 *what the mechanism is* and *where it lives*, with citations; the stack-agnostic probes for finding them are in [stack-probes.md](stack-probes.md).

| Mechanism | What to establish |
|---|---|
| Build system | Package manager, build tool, workspace/monorepo layout, where the app entry point is |
| Routing | How URLs map to pages: config-based route table, file-based routing, or manual registration — and where the full route list lives |
| API client layer | Where HTTP calls are made: a central client/service layer, generated clients, or scattered calls — and where base URLs and path constants live |
| i18n | Whether user-visible strings go through a catalog; catalog file locations and key convention — or that strings are hardcoded |
| Permission / feature gating | How UI elements are hidden or disabled: permission checks, role checks, feature flags — and where the gate definitions live |

## Signals, in order of value

**1. The route table.** Every registered route is a page a user can reach — the closest thing to a capability list the frontend has. Enumerate it completely before anything else; group routes by path prefix as the first draft of the frontend's capability view.

**2. Navigation and menu definitions.** Menus are the product's own grouping of its features, usually closer to business vocabulary than route paths are. Diffs between the menu and the route table are interesting in both directions: routes with no menu entry (deep links, admin corners, suspected dead pages) and menu entries gated off (features per tenant/role).

**3. The i18n string catalog.** The catalog is a literal list of everything the product says to users — the highest-density source of user vocabulary. Mine it for capability names, entity names, and action verbs. This feeds `ui-text-index.md` directly.

**4. The API client layer.** Every call site is one end of a stitch. Enumerate call sites and the endpoint each one hits (METHOD + path as the code constructs it, before normalization); this feeds `endpoint-index.md`. Calls constructed dynamically (path built from variables) get a `suspected` row with the construction site cited.

**5. Permission and feature-flag gates.** Reveal capability variations invisible in the route table: admin-only areas, per-tenant features, A/B experiments. Also the frontend's echo of the backend permission model — record the gate vocabulary in `glossary.md`.

## `ui-text-index.md` is a first-class artifact

The atlas's query entry point. Users describe features in the product's words ("cancel an order", "share with a group"); code speaks identifiers. Each row maps a user-visible string (i18n key or hardcoded literal) → the component/page rendering it → the owning capability. Fill it as a byproduct of every frontend pass: whenever a trace or inventory touches a labeled UI element, add its row. Template in [templates.md](templates.md).

## What counts as a UI entry

For chain purposes, a UI entry is the most specific user-reachable thing that starts the flow: a route/page for navigation-triggered flows, a button/menu-item/dialog-action for command-triggered ones. Cite the component that renders it and, for commands, the handler that fires the HTTP call.

## Dead capability detection, frontend flavor

Mark `suspected dead` (in `L1-capabilities.md`), do not delete: routes registered but unreachable from any menu or link, components behind permanently-off flags, i18n keys no component references, API call sites hitting endpoints the backend no longer registers (a stitch miss in `endpoint-index.md` is evidence).
