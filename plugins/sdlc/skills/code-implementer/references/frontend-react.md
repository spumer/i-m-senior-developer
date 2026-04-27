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
