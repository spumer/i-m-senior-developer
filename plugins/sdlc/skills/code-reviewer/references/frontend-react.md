# frontend-react.md — Code Reviewer: React-Specific Pitfalls

> **Angle:** review only. No implementation patterns, no design rationale.

## When to load

Load when the diff contains `*.tsx`, `*.jsx`, `*.ts` (React context), `*.vue`, or `*.svelte` files. Always load alongside `security.md` (never instead of it).

---

## XSS in React

React escapes JSX output by default. These patterns bypass the escape and are always review items:

**`dangerouslySetInnerHTML`:** Flag every usage. Require (a) justification why JSX cannot express the content, (b) explicit sanitization via `DOMPurify.sanitize()` before assignment. Unsanitized `dangerouslySetInnerHTML` is XSS.

**`href` / `src` / `action` with user-controlled value:** `javascript:` scheme executes on click. Flag any attribute populated from user-supplied data without scheme validation.

**`eval` / `Function()` at runtime:** `eval(userString)`, `new Function(userString)()`, `setTimeout(userString, 0)` — arbitrary code execution. Flag as critical.

**User-controlled URLs in `<img src>` / `<iframe src>`:** SSRF / tracking pixel / CSP bypass risk. Flag when URL comes from user data without domain allowlist.

**`window.location.href = userInput`:** Open redirect + `javascript:` execution. Flag when `userInput` is not validated against an allowlist of safe schemes/domains.

---

## CSP

If the application sets a `Content-Security-Policy` header (check `nginx.conf`, `_headers`, `middleware`, `meta http-equiv`):

- **`script-src 'unsafe-inline'`** — permits inline `<script>` and event handler attributes. Defeats CSP-based XSS protection. Flag as high finding.
- **`script-src 'unsafe-eval'`** — permits `eval()`, `Function()`, `setTimeout(string)`. Flag as high finding.
- **`default-src *`** — effective no-op CSP. Flag as medium finding.
- **New inline `<script>` tags** without a `nonce` attribute violate strict CSP. Flag if the project has CSP configured.
- **Inline event handlers as strings** (`<button onclick="doThing()">`) violate strict CSP. Flag; replace with React's `onClick={doThing}`.

---

## Accessibility (a11y)

Accessibility findings are medium priority — not blocking, but ship-quality issues:

**Interactive elements:**

`<div onClick={handler}>` — not keyboard accessible, not announced by screen readers as interactive. Flag; require `<button>` or `role="button"` with `tabIndex={0}` and `onKeyDown` handler (or just use `<button>`).

**Images:**

`<img src={...}>` without `alt` attribute → screen reader reads the filename. Flag all `<img>` without `alt`. Empty `alt=""` is correct for decorative images; a descriptive string for informative images.

**Form labels:**

`<input>` without associated `<label>` (either `htmlFor`/`id` pair, or `aria-label`, or `aria-labelledby`). Flag unlabeled form controls.

**Focus management on route change:**

Single-page apps that change route without moving focus leave screen reader users on the stale content. Flag if the diff adds a new route without focus management (at minimum, focus to the `<h1>` or a skip-nav landmark).

**ARIA roles:**

`role="button"` on a non-interactive element that still lacks `tabIndex` and keyboard handlers. Wrong ARIA is worse than no ARIA. Flag `role` usage that adds accessibility semantics without the matching behavior.

**Color contrast:** Not detectable from a diff, but flag new very-light CSS color values (`#aaa`, `rgba(0,0,0,0.3)`) as "verify WCAG AA contrast (4.5:1 for normal text)."

---

## Performance pitfalls

Performance findings are review items only when the pattern is a known regression path, not when "it could theoretically be faster":

**Missing `React.memo` for heavy components in lists:**

A component rendered inside a `map()` that re-renders on every parent state change, when its own props have not changed. Flag when: (a) the component is visually heavy or has expensive render logic, and (b) parent state updates frequently. Not every `map()` needs `memo` — only flag when the combination is clearly costly.

**New object/function created inline in JSX:**

```jsx
<Foo style={{ margin: 0 }} />           // new object every render
<Foo onClick={() => doThing(id)} />     // new function every render
```

These cause `React.memo` children to re-render unconditionally (referential inequality). Flag when `Foo` is `memo`-wrapped — the memoization becomes useless. Fix direction: extract to a variable outside JSX, or use `useMemo`/`useCallback`.

**`useMemo` / `useCallback` overuse:** The opposite — wrapping primitive computations (`useMemo(() => a + b, [a, b])`) adds overhead without savings. Flag when clearly premature; `useMemo`/`useCallback` are justified only when the bottleneck has been measured.

**Large bundle from `import *`:** `import * as Icons from 'lucide-react'` imports the entire library. Flag as medium; fix direction: named imports (`import { Home } from 'lucide-react'`).

---

## Hooks pitfalls

**`useEffect` with stale closures (missing deps):** The effect captures the initial value and never updates. Flag when a variable is used in the effect body but absent from the deps array, and the stale value will cause incorrect behavior. Fix: add to deps, or use a ref.

**Missing cleanup → memory leak / double-fire:** Any `useEffect` that creates subscriptions, timers (`setInterval`, `setTimeout`), or event listeners without a `return () => cleanup()` function. Flag as medium finding.

**`useState` initial value computed each render:** `useState(expensiveComputation())` — the computation runs on every render (initial value is discarded after mount). Flag when the call is clearly non-trivial; fix with lazy initializer: `useState(() => expensiveComputation())`.

**Custom hook called conditionally:** `if (condition) { const data = useMyHook(); }` — violates Rules of Hooks. React throws at runtime. Flag as critical.

---

## State management review

- **Local state in Redux** — `useSelector` to get a value that is only relevant to one component (e.g., an input's focus state). Overengineering per FPF A.11. Flag as design concern.
- **Cross-component state in props beyond 3 levels** — prop drilling. Flag as design concern: "state passed through N intermediate components; consider Context or Zustand."
- **State derived from props duplicated as state:**

```jsx
// Derived value stored as state — becomes stale when prop changes
const [fullName, setFullName] = useState(`${user.first} ${user.last}`);
```

The `fullName` state diverges from `user` after initial mount. Flag as medium finding: compute derived values inline or with `useMemo`, do not duplicate as state.

---

## Type-safety review

- **`any` / `unknown` without narrowing** — `const data: any = response.json()` used directly without type guard or cast with validation. Flag as medium.
- **`as` casts without justification** — `(foo as SomeType).field` → if `foo` could be something other than `SomeType` at runtime, the cast is a lie. Flag for audit; require a comment explaining why the cast is safe.
- **Missing prop types** — new component without a `Props` interface or type alias. Flag as minor; enforced by `tsc --noImplicitAny`.
- **`// @ts-ignore`** — suppresses type errors without explanation. Flag as minor; require `// @ts-expect-error` with a comment (stricter — fails if the error disappears).

---

## Test quality review

- **Snapshot tests as the only test** — `expect(rendered).toMatchSnapshot()` without any behavioral assertion. Snapshot breaks on any change (including intentional); provides no signal about what went wrong. Flag as low-signal test; require at least one behavioral assertion (does the button label say the right thing? Does the handler fire?).
- **Querying by class or id** — `container.querySelector('.submit-btn')` — brittle; breaks on CSS refactor. Flag as minor; fix direction: use `screen.getByRole('button', { name: /submit/i })` (accessibility-first query).
- **Missing user-event tests for interaction** — new button / input without a test that fires `userEvent.click()` or `userEvent.type()`. Flag as minor.
- **Mocked the component under test** — `jest.mock('./MyComponent')` in a test that is supposed to test `MyComponent`. The test is now a tautology. Flag as medium finding.

---

## Common review items

- **`console.log` left in production code** — flag as minor; remove before merge.
- **Commented-out code blocks** — flag as minor; code should live in git history, not in comments.
- **Magic numbers** — `if (items.length > 47)` — extract to a named constant. Flag as minor.
- **Missing error boundary** — a new asynchronous data-loading component without an `ErrorBoundary` wrapper. If the fetch fails, React will unmount the entire tree. Flag as medium for user-facing routes.
- **`useEffect` doing data-fetching directly** — `useEffect(() => { fetch(url).then(...) }, [])` instead of TanStack Query / SWR. Flag as design concern: mixing fetching with rendering lifecycle; no caching, no loading state standardization, no automatic retry. Fix direction: migrate to `useQuery`.
