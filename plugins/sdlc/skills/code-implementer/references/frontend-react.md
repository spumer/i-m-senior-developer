# frontend-react — implement angle

> **Angle:** implement only. Design rationale lives in
> `architect/references/frontend-react.md`. Review checklists live
> in `code-reviewer/references/frontend-react.md`.

## When to load

Load when `SKILL.md` stack-detection finds React markers (`package.json`
with `react` in dependencies, `*.tsx` / `*.jsx` source files,
`vite.config.*`, `next.config.*`).

## Project structure conventions

Follow the project's existing layout. If absent, recommend
feature-folder:

```
src/features/<name>/
  components/
  hooks/
  api.ts
  types.ts
  index.ts     # public API of the feature
src/shared/    # truly generic UI primitives only
```

Flat atomic (`components/`, `hooks/`, `pages/`) is acceptable for
small projects. Do not mix both conventions in one project.

## Component implementation patterns

Function components only — no class components in new code. Hooks at
the top level (never conditionally, never in loops — rules-of-hooks).

```tsx
export function UserCard({ userId }: { userId: string }) {
  const { data: user } = useUser(userId)
  if (!user) return null
  return <div>{user.name}</div>
}
```

Naming: `PascalCase` for components, `useFoo` for hooks. Pure
component rule: a component either owns its state OR receives it via
props — never both for the same state value (causes sync bugs).

## Hooks patterns

`useState` for independent scalars. `useReducer` when multiple values
update as a unit. `useEffect` cleanup — always return it for
subscriptions, timers, and event listeners:

```tsx
useEffect(() => {
  const sub = stream.subscribe(handler)
  return () => sub.unsubscribe()
}, [stream])
```

`useMemo` / `useCallback` only when measured (profiling shows
unnecessary re-renders). Adding them speculatively adds memo-check
overhead without benefit (FPF A.11).

Custom hooks: one responsibility per hook. A hook that fetches, formats,
and tracks UI state is doing too much — split it.

## Data fetching with TanStack Query

```tsx
// read
const { data, isLoading, error } = useQuery({
  queryKey: ['user', userId],
  queryFn: () => fetchUser(userId),
})

// write + invalidation
const mutation = useMutation({
  mutationFn: updateUser,
  onSuccess: () =>
    queryClient.invalidateQueries({ queryKey: ['user', userId] }),
})
```

Key convention: `[entity, id]` for single resource; `[entity, 'list',
filters]` for collections. Never fetch inside `useEffect` — that is
the pre-TanStack-Query pattern and introduces race conditions.

## TypeScript at component level

Props via `interface`:

```tsx
interface ButtonProps {
  label: string
  onClick: () => void
  disabled?: boolean
}
```

`ReactNode` for children (accepts elements, strings, fragments).
Generic components for reusable data-driven UI. `as const` for literal
unions. Avoid `any` — use `unknown` + type narrowing when the type is
not known at call-site.

## Testing with vitest + React Testing Library

```tsx
describe('UserCard', () => {
  it('renders user name', async () => {
    render(<UserCard userId="1" />)
    expect(await screen.findByText('Alice')).toBeInTheDocument()
  })
})
```

Query priority (accessibility-first): `getByRole` → `getByLabelText`
→ `getByText` → `getByTestId` (last resort). Avoid `getByClassName` /
`getByTag` — they test implementation, not behavior.

Use `userEvent` over `fireEvent` — simulates real browser event
sequences including focus, keyboard, pointer events.

Mock at the network boundary with `msw` (Mock Service Worker). Do not
mock the component under test — the test proves only that the mock
works, not the component.

## Runtime visual smoke (mandatory for UI changes)

RTL/vitest prove component logic and accessibility queries; they do NOT prove
the change renders in a real browser. Any change a user can SEE or interact with
(new/changed components, conditional hints, button enable/disable, i18n strings,
displayed state) requires a browser-level smoke of the affected scenario BEFORE
it is reported done. Type-checks and unit tests passing is necessary, not sufficient.

Verification ladder for render/UI artifacts units can't fully cover:
1. **Review** — read the diff against the design.
2. **Headless smoke** — launch the dev server, drive the affected scenario in a
   browser (Playwright; see the `webapp-testing` / `playwright-skill` skill if
   available), assert no console errors / no crash, confirm the expected state
   transition. For STABLE UI states, capture a screenshot as evidence.
3. **Live acceptance** — for animation/motion/canvas payoff a headless run cannot
   capture (animated-canvas frames come out black/frozen), do NOT claim visual
   success from a screenshot; state that the motion needs human acceptance and
   hand it off.

Scope the smoke to the changed scenario only — the broad post-merge sweep across
all flows is the planner's orchestration concern, not the implementer's DoD.
Record the smoke under "Commands run" in the report. If no browser tooling is
available, say so and downgrade explicitly to review + live-acceptance request —
do not silently report a UI change as verified on unit tests alone.

## Async patterns

`findBy*` queries auto-await element appearance (built-in `waitFor`):

```tsx
const heading = await screen.findByRole('heading', { name: 'Dashboard' })
```

`waitFor` for assertions requiring multiple retries. Avoid bare
`act()` in component tests — RTL's async utilities handle it
internally. Manual `act` usually signals the test is fighting the
framework.

## Integration with `document-skills:frontend-design`

For UI-fidelity (visual quality, design polish), activate
`document-skills:frontend-design`. If installed, it adds visual design
discipline (typography, spacing, component composition). If not
installed, graceful degrade to universal principles.

The implementation should reference the design system named in the ARCH
document (shadcn/ui, MUI, Tailwind, custom tokens). Do not introduce a
second design system without explicit architectural decision.

## Common implementation pitfalls

- **State updated in `useEffect` without guards** — creates re-render
  loops. Derive state from props or existing state instead.
- **Missing `useEffect` dependency array** — stale closures; effect
  reads outdated values. Use `exhaustive-deps` lint rule.
- **Testing implementation, not behavior** — if the test breaks on a
  pure refactor (no behavior change), it is testing the wrong thing.
- **Mocking the component under test** — tautology; proves the mock,
  not the behavior.
- **`any` type** — defeats TypeScript. Use `unknown` + narrowing, or
  a concrete interface. `any` at component boundaries removes type
  safety at the integration point.
- **Verifying with `tsc --noEmit` instead of the real build** — `tsc
  --noEmit` does not honor project references the way the CI build does,
  so it can report 0 errors while `npm run build` (typically `tsc -b &&
  vite build`) fails. Before hand-off run the build command CI runs
  (check `package.json` scripts / the deploy target), not a substitute
  type-check.
- **Ignoring your own diagnostic anomaly** — if a grep / type-check /
  quick script you ran prints something unexpected (an unused import, a
  symbol used but not imported, `imports X: False`), resolve it before
  committing. It is evidence, not noise (FPF A.10) — a silently-failed
  `Edit` surfaces here first.
