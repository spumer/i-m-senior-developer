# frontend-react — design angle

> Design decisions for React (and Vue/Svelte by extension — the principles transfer) frontends. This file covers the **design angle only**: which framework, how to draw component boundaries, where state lives, how data fetching is architected, routing design. No vitest patterns, no RTL, no hooks implementation — those are implement angle. No XSS/CSP/accessibility audit — that is review angle.

## When to load

Load when SKILL.md stack-detection finds React, Next.js, Vue, Svelte, or SolidJS markers in `package.json` and the design touches components, state, routing, or rendering boundaries.

## Framework decision matrix

Pick based on rendering requirements and SEO constraints. Do not pick a framework because it is popular — pick it because the stated requirements demand its features.

| Framework | When to pick | When to avoid |
|---|---|---|
| **React + Vite (SPA)** | Pure client-rendered app; dashboard, admin panel, logged-in-only tool; SEO not required | Public-facing pages with SEO requirements; content sites |
| **Next.js (App Router)** | SSR/SSG needed; SEO required; full-stack in one repo (API routes + frontend); large team with convention needs | Tiny app where App Router complexity is not justified; team unfamiliar with RSC mental model |
| **Vue 3 + Vite** | Team knows Vue; composable-first design; progressive adoption into existing HTML | React ecosystem lock-in needed; large team already standardized on React |
| **SvelteKit** | SSR/SSG + minimal bundle; team wants compiler-based reactivity | React-heavy organization; large ecosystem dependency |
| **SolidJS** | Fine-grained reactivity needed; performance-critical rendering | Team unfamiliar with signals mental model; broad ecosystem needed |

**Decision rule (FPF A.11):** SSR/SEO requirements → Next.js or SvelteKit. Pure dashboard/admin (logged-in only, no SEO) → SPA with React + Vite. Do not add server-side rendering complexity to a project where it is not needed.

## Component boundaries

Component boundaries are the frontend analogue of bounded contexts. Getting them wrong early means either a monolithic component (hundreds of lines, one test-impossible unit) or over-fragmented atoms (dozens of components coordinated by invisible props).

**Atomic design vs feature-folder:**
- **Atomic design** (atoms → molecules → organisms → templates → pages): useful when a design system is the primary output; harder to colocate feature logic
- **Feature-folder** (each feature owns its components, hooks, and types): scales better for application code where features are the primary unit of change

Design decision: pick one and name it in the architecture document. Mixed conventions are worse than either alone.

**Boundary rule:** A component either **owns its state** (stateful/container) or **receives it via props** (presentational/pure). It does not do both. When a component owns state and also accepts conflicting state via props, the design has a seam error — there are actually two components fused together. Name the seam explicitly in the architecture.

**Colocate what changes together.** If a component and its hook always change together, they are one boundary. If the hook is shared across features, it belongs at a shared layer named in the architecture.

## State management decision

State management is a design decision. The correct tier is the simplest one that meets the stated requirements.

```
Is the state local to one component?
  └── YES → useState (or useReducer for complex transitions)

Is the state shared across a small subtree (≤3 levels)?
  └── YES → React Context + useContext

Is the state shared across features or routes?
  ├── Small/medium app (1-5 features) → Zustand or Jotai
  └── Large app, strict patterns, large team → Redux Toolkit

Is the state derived entirely from server data?
  └── YES → TanStack Query owns it (no separate client state needed)
```

**Anti-pattern:** Redux for a 5-component app. Redux introduces actions, reducers, selectors, and store configuration. For a small app this is more cognitive load than the problem it solves — FPF A.11 applies.

**Design output:** The architecture document must name the state management tier chosen and state which features/contexts use it. "We'll decide later" is a design defect — the choice affects component boundaries, testing strategy, and onboarding.

## Data fetching architecture

Where data is fetched and how it is cached are design decisions that affect every component in the feature.

| Approach | When to use |
|---|---|
| **TanStack Query (React Query)** | Client-side data fetching with caching, background refetch, optimistic updates; most SPA use cases |
| **SWR** | Simpler use case than TanStack Query; team prefers minimal API; Next.js projects (SWR is by Vercel) |
| **RSC (React Server Components)** | Next.js App Router; data needed at render time, not post-mount; reduces client bundle |
| **Hand-rolled fetch hooks** | One-off internal tools; deliberate choice to avoid a library dependency |

**Design decisions to document:**
- Where does the cache live? (TanStack Query client, SWR cache, React context, or none)
- What invalidates the cache after a mutation? Name the cache keys and the invalidation triggers.
- Who owns the loading/error state? Name it in the architecture, not in the component.

**Anti-pattern:** Putting `fetch()` directly in `useEffect` inside a component. This couples the component to the network, makes the data unavailable to other components, and defeats caching. The architecture should name a data-layer hook or RSC for each data source.

## Routing architecture

Routing decisions belong in the architecture, not discovered during implementation.

**Design output required:**
- List of all routes (path + component + auth requirement)
- Auth guards per route (which routes require authentication; what happens on unauthorized access)
- Layout boundaries (which routes share a layout shell; where layout nesting begins)
- Route-level code splitting (which routes are lazy-loaded vs eagerly bundled)

| Router | When to use |
|---|---|
| **React Router v6** | SPA with client-side routing; flexible configuration; no SSR |
| **Next.js file-based routing** | Next.js project; convention over configuration; App Router for nested layouts |
| **TanStack Router** | Type-safe routes; complex route search params; team values type safety at routing layer |

**Decision rule:** Match the router to the framework. Do not mix React Router and Next.js file routing in the same project. Document the chosen router and the route list in the architecture before implementation.

## Type system at boundaries

Types at boundaries prevent contract drift between backend and frontend. This is a design decision, not a coding task.

**Options:**
- **OpenAPI codegen:** Backend publishes an OpenAPI spec; frontend generates TypeScript types from it. Best for teams where backend and frontend can agree on a spec-first workflow (see `references/api-design.md`).
- **GraphQL codegen (GraphQL Code Generator):** Schema drives type generation for both query types and operation types.
- **Zod schemas (hand-written):** Frontend defines its own runtime-validated types; backend contract is implicit. Simpler for small projects; types drift as the API evolves.
- **Hand-written TypeScript interfaces:** No generation, no runtime validation; lowest setup cost, highest maintenance cost at scale.

**Design output:** The architecture document must state:
- Where types are generated (and from what source)
- Where types are hand-written (and who is responsible for keeping them in sync)
- Where generated and hand-written types meet (if both exist)

Leaving this undefined produces "we added a field to the backend and the frontend silently ignores it" bugs.

## Integration with `document-skills:frontend-design`

For UI-fidelity — visual quality, design polish, typography, spacing, component composition — activate `document-skills:frontend-design`. If installed, it adds visual design discipline at design time: which design system to use, what the visual primitives are, how components compose visually, what the taste constraints are.

If `document-skills:frontend-design` is not installed, graceful degrade to universal principles (consistent spacing scale, readable typography, accessible color contrast).

Regardless of whether the skill is installed, the architecture document must name:
- The design system (e.g. shadcn/ui, MUI, Radix UI, custom Tailwind)
- The CSS strategy (Tailwind utility classes, CSS Modules, styled-components, vanilla CSS)
- The visual primitives at design time (so the implementer does not invent them)

## Common design pitfalls

- **Redux by default.** Redux is a state management architecture, not a default. Most applications do not need it. When in doubt, start with Zustand or React Context and escalate only if the complexity of the state graph demands it.

- **Prop-drilling beyond 3 levels.** Passing the same prop through 4+ layers of components that do not use it is a seam error: the state belongs at a shared layer. The architecture should name the shared layer rather than leaving it to the implementer to discover at depth 5.

- **Fetch in components.** Putting data-fetching logic directly in component bodies (via `useEffect` or top-level `await`) couples the rendering to the network. The architecture should name the data-fetching layer explicitly so components receive data, not fetch it.

- **Ignoring the SSR/CSR boundary.** In Next.js App Router or SvelteKit, the boundary between server-rendered and client-rendered components is a design seam, not an implementation detail. Crossing it incorrectly produces hydration mismatches that are hard to debug. Name the RSC/client boundary in the architecture document.

- **Designing without naming the design system.** Leaving the design system undefined means every implementer makes their own choice. The result is an inconsistent UI. The architecture document must name the design system even for internal tools.

- **Co-locating state and fetch in one component.** A component that fetches its own data and holds local state for UI interactions is two components fused together. The architecture should separate the data-layer boundary from the presentation boundary.

## Design checklist for React/frontend projects

Before finalizing the architecture document for a React frontend, verify:

- [ ] Framework chosen with a stated reason (SPA vs SSR vs SSG)
- [ ] Component boundary strategy named (atomic design vs feature-folder)
- [ ] State management tier chosen for each feature (local / context / Zustand / Redux)
- [ ] Data-fetching layer named (TanStack Query / SWR / RSC / hand-rolled)
- [ ] Cache invalidation strategy documented for mutations
- [ ] Route list and auth-guard requirements documented
- [ ] Type system at API boundary declared (codegen vs hand-written)
- [ ] Design system named (shadcn/ui, MUI, Radix, custom Tailwind, etc.)
- [ ] CSS strategy named (Tailwind, CSS Modules, styled-components)
- [ ] RSC/CSR boundary drawn if using Next.js App Router
