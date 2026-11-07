# HerSpace — React Frontend Architecture

| Field | Value |
|---|---|
| Document ID | HS-FE-001 |
| Version | 1.0 |
| Date | 2026-10-31 |
| Stack | React 18 + JavaScript (JSX), Vite, React Router, TanStack Query, Axios, Recharts, date-fns |
| Traces to | `wireframes.md` §19 (route map), `api-documentation.md` |
| Consumed by | `roadmap.md` |

---

## 1. Stack decisions

| Concern | Decision | Why |
|---|---|---|
| Build tool | **Vite** | Fast dev server, small production bundles, first-class JSX |
| Language | **JavaScript + JSX** with JSDoc typedefs | Matches the brief; avoids a TS migration as a prerequisite |
| Routing | **React Router v6** (data router) | Nested layouts, loaders optional, route-level code splitting |
| Server state | **TanStack Query v5** | Cache, retries, invalidation, request dedupe, background refetch |
| Client state | React Context (session, theme, toasts) | Small, global, rarely changing |
| HTTP | **Axios** instance with CSRF + error normaliser | Interceptors keep components free of transport logic |
| Forms | **react-hook-form** + **zod** resolvers | Mirrors server validation, minimal re-renders, accessible errors |
| Charts | **Recharts** | Declarative SVG, accessible table fallbacks are easy to pair |
| Dates | **date-fns** (+ `date-fns-tz`) | Timezone-aware formatting, tree-shakeable |
| Styling | **CSS Modules + CSS custom properties** | No utility framework; design tokens are the contract |
| Icons | Inline SVG components (own set, 20/24 px) | No icon font, no runtime CDN |
| Fonts | Self-hosted `woff2` (Manrope, Inter) | Privacy: no third-party font CDN (NFR-PRIV-02) |
| Tests | Vitest + Testing Library; Playwright for E2E | Fast unit tests + real browser journeys |
| Lint/format | ESLint (`react`, `jsx-a11y`, `import`) + Prettier | Accessibility linting is non-negotiable |

**Explicitly not used:** TypeScript, Next.js/SSR, Redux, Tailwind, styled-components, Moment, any analytics SDK, any remote font or image CDN.

**Dependencies (production):**
```
react react-dom react-router-dom @tanstack/react-query axios react-hook-form zod
@hookform/resolvers recharts date-fns date-fns-tz
```
**Dev:** `vite @vitejs/plugin-react vitest @testing-library/react @testing-library/user-event @testing-library/jest-dom jsdom eslint prettier eslint-plugin-jsx-a11y playwright`

---

## 2. Directory structure

```text
frontend/
├── public/
│   ├── favicon.svg
│   └── fonts/                        # Manrope + Inter woff2, self-hosted
├── src/
│   ├── main.jsx                      # bootstrap: QueryClient, Router, ThemeBoot
│   ├── App.jsx                       # route table
│   ├── assets/
│   │   └── icons/                    # inline SVG React components
│   ├── components/
│   │   ├── ui/                       # Button, Card, TextField, Toggle, ChipGroup,
│   │   │                             # StatusPill, EmptyState, Skeleton, InlineAlert,
│   │   │                             # ConfirmDialog, Sheet, Tabs, Toast, Avatar
│   │   ├── layout/                   # AppShell, SidebarNav, BottomNav, MoreSheet, TopBar
│   │   ├── charts/                   # LineChart, BarChart, ChartTable, ProgressRing
│   │   ├── wellness/                 # EmotionPicker, IntensitySlider, TriggerPicker,
│   │   │                             # MoodCalendar, MoodDayCell, MoodTrendStrip
│   │   ├── people/                   # ContactCard, ContactStatusPill, InviteDialog,
│   │   │                             # SupportTypePicker, SharePicker, SharePreview
│   │   ├── journal/                  # EntryListItem, EntryEditor, TagInput, PromptCard
│   │   ├── selfcare/                 # RoutineCard, RoutineItemRow, WeekdayPicker,
│   │   │                             # CompletionGrid
│   │   ├── calm/                     # BreathePacer, GroundingSteps, MeditationTimer,
│   │   │                             # AffirmationDeck
│   │   ├── insights/                 # MetricTile, StatementList, ComparisonRow
│   │   └── privacy/                  # ConsentRow, ExportStatus, DeleteAccountForm
│   ├── layouts/
│   │   ├── PublicLayout.jsx          # welcome/auth/public token pages
│   │   ├── AppLayout.jsx             # sidebar + top bar + outlet
│   │   └── SettingsLayout.jsx        # settings sub-nav + outlet
│   ├── pages/
│   │   ├── auth/                     # Welcome, Register, Login, ForgotPassword,
│   │   │                             # ResetPassword, VerifyEmail, VerificationGate
│   │   ├── onboarding/               # Profile, Wellness, Notifications, People, Privacy
│   │   ├── app/                      # Dashboard, Notifications
│   │   ├── mood/                     # MoodHome (history), CheckIn, Calendar, Detail
│   │   ├── people/                   # PeopleList, ContactForm, ContactDetail, Invitations
│   │   ├── support/                  # SupportNew, SupportList, SupportDetail
│   │   ├── journal/                  # JournalList, EntryNew, EntryEdit, EntryDetail,
│   │   │                             # Gratitude, Prompts
│   │   ├── selfcare/                 # SelfCareHome, RoutineForm, RoutineDetail, History
│   │   ├── calm/                     # CalmHome, Breathing, Grounding, Meditation,
│   │   │                             # Affirmations
│   │   ├── insights/                 # InsightsHome, Weekly, Monthly
│   │   ├── settings/                 # Profile, Security, Privacy, Notifications, Data, Delete
│   │   └── public/                   # Privacy, Terms, SupportResources, InvitationResponse,
│   │                                 # SupportResponse, NotFound
│   ├── services/
│   │   ├── http.js                   # axios instance, CSRF, error normalisation
│   │   ├── auth.js  profile.js  moods.js  contacts.js  support.js  journal.js
│   │   ├── selfcare.js  calm.js  insights.js  notifications.js  privacy.js
│   │   └── queryKeys.js              # single source of cache keys
│   ├── hooks/
│   │   ├── useSession.js  useTheme.js  useMediaQuery.js  useReducedMotion.js
│   │   ├── useUnsavedChanges.js  useDebouncedValue.js  useFocusTrap.js
│   │   ├── useMoods.js  useContacts.js  useJournal.js  useRoutines.js
│   │   └── useCalmTimer.js           # timestamp-based timer, background-safe
│   ├── context/
│   │   ├── SessionContext.jsx        # user, onboarding_required, refresh()
│   │   ├── ThemeContext.jsx          # preference + resolved theme
│   │   └── ToastContext.jsx          # single aria-live region
│   ├── styles/
│   │   ├── tokens.css                # design tokens (light + dark)
│   │   ├── reset.css                 # modern reset
│   │   ├── global.css                # base typography, focus, scrollbars
│   │   └── utilities.css             # visually-hidden, stack, cluster
│   └── test/
│       ├── setup.js
│       └── fixtures/
├── index.html
├── vite.config.js
├── .env.example                      # VITE_API_BASE_URL=/api/v1
└── package.json
```

**Rules**
- `pages/` may import from `components/`, `hooks/`, `services/`; never the reverse.
- `components/ui/` has no knowledge of HerSpace domains (no API imports).
- One page component per route; data fetching lives in hooks, not in JSX.
- No default exports for components except pages (lazy loading requires default exports).

---

## 3. Routing and guards

### 3.1 Route table (matches `wireframes.md` §19)

```jsx
<Routes>
  <Route element={<PublicLayout />}>
    <Route path="/" element={<Welcome />} />
    <Route path="/register" element={<Register />} />
    <Route path="/login" element={<Login />} />
    <Route path="/forgot-password" element={<ForgotPassword />} />
    <Route path="/reset-password/:token" element={<ResetPassword />} />
    <Route path="/verify-email/:token" element={<VerifyEmail />} />
    <Route path="/confirm-email-change/:token" element={<ConfirmEmailChange />} />
    <Route path="/privacy" element={<Privacy />} />
    <Route path="/terms" element={<Terms />} />
    <Route path="/support-resources" element={<SupportResources />} />
    <Route path="/invitation/:token" element={<InvitationResponse />} />
    <Route path="/support-response/:token" element={<SupportResponse />} />
  </Route>

  <Route element={<RequireAuth />}>
    <Route path="/onboarding/:step" element={<OnboardingLayout />}>
      <Route path="profile" element={<OnboardingProfile />} />
      <Route path="wellness" element={<OnboardingWellness />} />
      <Route path="notifications" element={<OnboardingNotifications />} />
      <Route path="people" element={<OnboardingPeople />} />
      <Route path="privacy" element={<OnboardingPrivacy />} />
    </Route>

    <Route path="/app" element={<AppLayout />}>
      <Route index element={<Dashboard />} />
      <Route path="notifications" element={<Notifications />} />

      <Route path="mood" element={<MoodHome />} />
      <Route path="mood/check-in" element={<CheckIn />} />
      <Route path="mood/calendar" element={<MoodCalendar />} />
      <Route path="mood/:id" element={<MoodDetail />} />

      <Route path="people" element={<PeopleList />} />
      <Route path="people/new" element={<ContactForm />} />
      <Route path="people/:id" element={<ContactDetail />} />
      <Route path="people/:id/edit" element={<ContactForm />} />
      <Route path="invitations" element={<Invitations />} />

      <Route path="support" element={<SupportList />} />
      <Route path="support/new" element={<SupportNew />} />
      <Route path="support/:id" element={<SupportDetail />} />

      <Route path="journal" element={<JournalList />} />
      <Route path="journal/new" element={<EntryNew />} />
      <Route path="journal/gratitude" element={<Gratitude />} />
      <Route path="journal/prompts" element={<Prompts />} />
      <Route path="journal/:id" element={<EntryDetail />} />
      <Route path="journal/:id/edit" element={<EntryEdit />} />

      <Route path="selfcare" element={<SelfCareHome />} />
      <Route path="selfcare/new" element={<RoutineForm />} />
      <Route path="selfcare/history" element={<RoutineHistory />} />
      <Route path="selfcare/:id" element={<RoutineDetail />} />
      <Route path="selfcare/:id/edit" element={<RoutineForm />} />

      <Route path="calm" element={<CalmHome />} />
      <Route path="calm/breathing/:slug" element={<Breathing />} />
      <Route path="calm/grounding" element={<Grounding />} />
      <Route path="calm/meditation" element={<Meditation />} />
      <Route path="calm/affirmations" element={<Affirmations />} />

      <Route path="insights" element={<InsightsHome />} />
      <Route path="insights/weekly" element={<WeeklyReport />} />
      <Route path="insights/monthly" element={<MonthlyReport />} />

      <Route path="settings" element={<SettingsLayout />}>
        <Route index element={<Navigate to="profile" replace />} />
        <Route path="profile" element={<SettingsProfile />} />
        <Route path="security" element={<SettingsSecurity />} />
        <Route path="privacy" element={<SettingsPrivacy />} />
        <Route path="notifications" element={<SettingsNotifications />} />
        <Route path="data" element={<SettingsData />} />
        <Route path="delete" element={<SettingsDelete />} />
      </Route>
    </Route>
  </Route>

  <Route path="*" element={<NotFound />} />
</Routes>
```

### 3.2 Guard behaviour

```jsx
function RequireAuth() {
  const { status, user, onboardingRequired } = useSession();
  const location = useLocation();
  if (status === "loading") return <FullPageSkeleton />;
  if (status === "anonymous") {
    return <Navigate to={`/login?next=${encodeURIComponent(location.pathname)}`} replace />;
  }
  if (user?.deletionScheduledFor) return <Navigate to="/app/settings/delete" replace />;
  if (onboardingRequired && !location.pathname.startsWith("/onboarding")) {
    return <Navigate to="/onboarding/profile" replace />;
  }
  return <Outlet />;
}
```

- `/app/settings/delete` is reachable while deletion is scheduled (so the user can see status).
- Unverified users are **not** redirected; `AppLayout` renders `VerificationGate` for private modules (the API returns `403 email_not_verified`).
- After login, `?next=` is honoured only if it starts with `/` and not `//` (open-redirect guard).
- 404 for unknown routes inside `/app` renders inside the shell.

### 3.3 Code splitting

```jsx
const JournalList = lazy(() => import("../pages/journal/JournalList"));
```
Split at route level. Prefetch on hover/focus of nav links via `import()` in `onMouseEnter`. Keep the initial bundle ≤250 KB gzipped (NFR-PERF-02).

---

## 4. State management

### 4.1 Layers

| Layer | Holds | Tool |
|---|---|---|
| Server state | Moods, journal, contacts, routines, notifications, insights | TanStack Query |
| Session | user, email_verified, onboarding_required, deletion status | `SessionContext` + `/auth/session/` |
| UI preference | theme, reduced motion (server-persisted, cached locally) | `ThemeContext` |
| Ephemeral UI | dialogs, toasts, unsaved-changes prompts | Local state + `ToastContext` |
| Form state | field values, errors, dirty | react-hook-form |

No global store for domain data. No duplicated server data in Context.

### 4.2 Query keys (single source)

```js
// services/queryKeys.js
export const qk = {
  session: ["session"],
  profile: ["profile"],
  preferences: ["preferences"],
  moods: (filters = {}) => ["moods", filters],
  mood: (id) => ["moods", "detail", id],
  moodCalendar: (year, month) => ["moods", "calendar", year, month],
  moodInsights: (period, anchor) => ["moods", "insights", period, anchor],
  emotions: ["reference", "emotions"],
  triggers: ["moods", "triggers"],
  contacts: (filters = {}) => ["contacts", filters],
  contact: (id) => ["contacts", "detail", id],
  invitations: (contactId) => ["invitations", contactId],
  support: (filters = {}) => ["support", filters],
  supportDetail: (id) => ["support", "detail", id],
  journal: (filters = {}) => ["journal", filters],
  journalEntry: (id) => ["journal", "detail", id],
  journalTags: ["journal", "tags"],
  prompts: (category) => ["reference", "prompts", category],
  routines: ["routines"],
  routine: (id) => ["routines", "detail", id],
  today: (localDate) => ["routines", "today", localDate],
  completions: (filters) => ["routines", "completions", filters],
  calmActivities: (kind) => ["calm", "activities", kind],
  affirmations: (filters) => ["calm", "affirmations", filters],
  calmSessions: (filters) => ["calm", "sessions", filters],
  insightsWeekly: (weekStart) => ["insights", "weekly", weekStart],
  insightsMonthly: (month) => ["insights", "monthly", month],
  insightsOverview: (range) => ["insights", "overview", range],
  notifications: (filters) => ["notifications", filters],
  unreadCount: ["notifications", "unread-count"],
  consents: ["privacy", "consents"],
  exports: ["privacy", "exports"],
  deletion: ["privacy", "deletion"],
  resources: (region) => ["reference", "resources", region],
};
```

**Invalidation rules**
| Mutation | Invalidate |
|---|---|
| Save mood | `moods`, `mood(id)`, `moodCalendar`, `moodInsights`, `today` |
| Create/edit/delete journal | `journal`, `journalEntry(id)`, `journalTags`, `insights*` |
| Contact create/update/delete | `contacts`, `contact(id)` |
| Invite/respond | `contacts`, `invitations`, `notifications` |
| Support create/cancel/revoke | `support`, `supportDetail(id)`, `notifications` |
| Routine create/update/delete | `routines`, `routine(id)`, `today` |
| Complete routine | `today`, `completions`, `insights*` |
| Calm session | `calmSessions`, `insights*` |
| Consent change | `consents`, `preferences`, `supportDetail` |
| Export request | `exports` (poll `refetchInterval` while queued/processing) |

### 4.3 Query defaults

```js
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 5 * 60_000,
      retry: (count, err) => count < 2 && !err.isAuthError && err.status !== 404,
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
    },
    mutations: { retry: 0 },
  },
});
```

- Reference data (`emotions`, `prompts`, `calm activities`, `resources`): `staleTime: 60 * 60_000`.
- Export status: `refetchInterval: (data) => (data?.status === "queued" || data?.status === "processing" ? 3000 : false)`.
- Unread count: `refetchInterval: 60_000`, paused when the tab is hidden.

---

## 5. HTTP layer

### 5.1 Axios instance

```js
// services/http.js
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api/v1",
  withCredentials: true,
  timeout: 20_000,
  headers: { "Content-Type": "application/json" },
});

function readCookie(name) {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
}

api.interceptors.request.use((config) => {
  const method = (config.method ?? "get").toUpperCase();
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const token = readCookie("csrftoken");
    if (token) config.headers["X-CSRFToken"] = decodeURIComponent(token);
  }
  config.headers["X-Request-ID"] = crypto.randomUUID();
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => Promise.reject(normaliseError(error))
);

export default api;
```

### 5.2 Error normalisation

```js
// services/http.js (continued)
export class ApiError extends Error {
  constructor({ status, code, message, fields, requestId }) {
    super(message);
    this.status = status;
    this.code = code;
    this.fields = fields ?? {};
    this.requestId = requestId;
    this.isAuthError = status === 401;
  }
}

function normaliseError(error) {
  if (error.response) {
    const { status, data, headers } = error.response;
    const body = data?.error ?? {};
    return new ApiError({
      status,
      code: body.code ?? "server_error",
      message: body.message ?? defaultMessage(status),
      fields: body.fields,
      requestId: body.request_id ?? headers["x-request-id"],
    });
  }
  return new ApiError({
    status: 0,
    code: navigator.onLine ? "network_error" : "offline",
    message: navigator.onLine
      ? "We couldn't reach HerSpace. Please try again."
      : "You're offline. Changes aren't saved.",
  });
}
```

**Rules**
- Components never read `error.response`; they use `error.code`, `error.fields`, `error.status`.
- `401` anywhere triggers `SessionContext.refresh()` once and routes to `/login?next=`.
- `403 email_not_verified` renders `VerificationGate`, never a generic error.
- `429` shows `Retry-After` in human words ("Try again in 2 minutes").
- `409 edit_conflict` opens a "reload current version" dialog.

### 5.3 CSRF bootstrap

`main.jsx` calls `GET /auth/csrf/` before mounting the router. The cookie is set; the interceptor reads it. If a state-changing request returns `403 CSRF`, the client refetches `/auth/csrf/` and retries once.

---

## 6. Session and theme

### 6.1 Session bootstrap

```jsx
// context/SessionContext.jsx (shape)
const [state, setState] = useState({ status: "loading", user: null, onboardingRequired: false });

useEffect(() => {
  api.get("/auth/session/")
    .then(({ data }) => setState({
      status: "authenticated",
      user: data.user,
      onboardingRequired: data.onboarding_required,
      deletionScheduledFor: data.deletion_scheduled_for,
    }))
    .catch((err) => {
      if (err.status === 401) setState({ status: "anonymous", user: null });
      else setState({ status: "error", user: null, error: err });
    });
}, []);
```

`refresh()` is called after login, logout, email verification, onboarding completion, and password change.

### 6.2 Theme without flash

`index.html` contains a blocking inline script (allowed by CSP hash) that applies the cached theme before paint:

```html
<script>
  (function () {
    try {
      var t = localStorage.getItem("hs-theme") || "system";
      var dark = t === "dark" || (t === "system" && matchMedia("(prefers-color-scheme: dark)").matches);
      document.documentElement.dataset.theme = dark ? "dark" : "light";
    } catch (e) {}
  })();
</script>
```

On session load, the server preference wins and is written to `localStorage`. `ThemeContext` listens to `prefers-color-scheme` changes when the preference is `system`.

### 6.3 Reduced motion

```js
const systemReduced = useMediaQuery("(prefers-reduced-motion: reduce)");
const reduced = systemReduced || preferences.reduced_motion;
```
`data-reduced-motion="true"` on `<html>` disables transitions and switches the breathing pacer to its static variant.

---

## 7. Component architecture

### 7.1 Layering

```
pages/  →  domain components (wellness/, journal/, …)  →  ui/ primitives  →  styles/tokens.css
```
- Pages own data fetching and URL state.
- Domain components are presentational + local interaction (e.g. `EmotionPicker` toggling selection).
- `ui/` primitives are domain-agnostic, fully keyboard-accessible, and tested in isolation.

### 7.2 Key component contracts

| Component | Props (shape) | Behaviour |
|---|---|---|
| `Button` | `variant`, `size`, `loading`, `disabled`, `iconLeft`, `iconRight`, `as` | 44 px min height, `aria-busy` when loading, never disabled without an adjacent reason |
| `TextField` | `label`, `hint`, `error`, `maxLength`, `showCounter`, `required` | Generates ids, wires `aria-describedby`/`aria-invalid` |
| `ChipGroup` | `options`, `value`, `onChange`, `multiple`, `max` | `role="group"`, `aria-pressed`, roving tabindex |
| `IntensitySlider` | `value`, `onChange` | Native `<input type="range">`, numeric output, `aria-valuetext="6 of 10"` |
| `StatusPill` | `status`, `label` | Text + icon; colours from a fixed map, never colour-only |
| `ConfirmDialog` | `open`, `title`, `description`, `confirmLabel`, `requireText`, `onConfirm` | Focus trap, Escape cancels, confirm disabled until text matches |
| `Sheet` | `open`, `onClose`, `title` | Mobile modal with drag handle; `aria-modal` |
| `MoodCalendar` | `year`, `month`, `days`, `onSelect` | `role="grid"`, arrow keys, `aria-label` per cell |
| `ChartTable` | `columns`, `rows`, `caption` | Visually hidden on desktop, expandable "View as table" |
| `BreathePacer` | `pattern`, `cycles`, `reduced`, `onPhaseChange` | Timestamp-driven phases, pause/resume |
| `useCalmTimer` | `durationSeconds` | Computes elapsed from `performance.now()`; survives tab backgrounding |
| `EmptyState` | `title`, `body`, `action` | Exactly one action |

### 7.3 Example: emotion picker

```jsx
export function EmotionPicker({ emotions, selected, onToggle, max = 12 }) {
  const atMax = selected.length >= max;
  return (
    <fieldset className={styles.group}>
      <legend className={styles.legend}>Emotions</legend>
      {["pleasant", "unpleasant", "neutral"].map((category) => (
        <div key={category} className={styles.row}>
          <span className={styles.category}>{categoryLabel(category)}</span>
          {emotions.filter((e) => e.category === category).map((emotion) => {
            const isOn = selected.includes(emotion.key);
            return (
              <button
                key={emotion.key}
                type="button"
                aria-pressed={isOn}
                disabled={!isOn && atMax}
                onClick={() => onToggle(emotion.key)}
                className={cx(styles.chip, isOn && styles.on)}
              >
                {emotion.label}
              </button>
            );
          })}
        </div>
      ))}
      <p className={styles.counter} aria-live="polite">
        {selected.length} of {max} selected
      </p>
    </fieldset>
  );
}
```

### 7.4 Forms

- `react-hook-form` with `zodResolver`; zod schemas mirror server rules (`frontend/src/services/schemas.js`).
- Server field errors are mapped back with `setError(field, { message })`.
- On `409 edit_conflict`, the dialog offers "Load current version" (refetch and reset) or "Keep mine" (resubmit with new `expected_updated_at`).
- Unsaved changes: `useUnsavedChanges` blocks in-app navigation via the router blocker and warns on `beforeunload` for the journal editor only.

---

## 8. Charts and data display

| Chart | Component | Accessibility |
|---|---|---|
| Mood intensity over time | `LineChart` (no area fill, dots + line) | `ChartTable` + summary sentence |
| Emotion frequency | horizontal `BarChart` | ordered list fallback |
| Routine completion grid | `CompletionGrid` (divs, not canvas) | each cell is a labelled element |
| Weekly check-in strip | `MoodTrendStrip` | text summary |

Rules
- No red/green mood encoding; intensity uses the violet→sage ramp from `wireframes.md` §2.2.
- Axis labels use `--text-faint` at ≥4.5:1.
- Charts never animate on scroll; one 200 ms draw on mount unless reduced motion.
- Every chart has a `<figcaption>` and a table equivalent behind a disclosure.

---

## 9. Accessibility implementation

| Requirement | Implementation |
|---|---|
| Skip link | First child of `AppShell`, visually hidden until focused |
| Landmarks | `header`, `nav[aria-label="Main"]`, `main#main`, `footer` on public pages |
| Focus management | On route change, focus `main` and announce the page title via `aria-live` |
| Modals | `useFocusTrap`, `aria-modal="true"`, restore focus to the trigger |
| Live regions | One `ToastContext` region (`aria-live="polite"`), one route announcer (`aria-live="assertive"` for errors only) |
| Errors | Field-level `role="alert"` only after submit attempt; `aria-invalid` toggled |
| Keyboard | All interactions operable; drag-reorder has Alt+↑/↓ alternative |
| Reduced motion | CSS `@media (prefers-reduced-motion: reduce)` + `data-reduced-motion` |
| Contrast | Token pairs tested in CI; no opacity-based text |
| Zoom | Layout uses `rem`/`clamp`; no fixed heights on text containers |
| Charts | Table fallback + text summary |

**Testing:** `eslint-plugin-jsx-a11y` at error level; `jest-axe` assertions on every `ui/` component; Playwright keyboard journeys for check-in, support request, journal editor, and settings.

---

## 10. Performance

| Technique | Detail |
|---|---|
| Route splitting | `React.lazy` per page; shared vendor chunk |
| Prefetch | Nav hover/focus triggers dynamic import |
| Images | None in core flows; icons are inline SVG |
| Fonts | Two weights per family, `font-display: swap`, preload only the body regular |
| Query caching | `staleTime` 30 s for user data, 1 h for reference |
| List rendering | Paginated (20), no virtualization in v1 (max 100/page) |
| Debounce | Journal search 300 ms; theme PATCH 400 ms |
| Bundle budget | Initial ≤250 KB gzip; CI fails above 275 KB |
| Lighthouse | LCP ≤2.5 s, CLS ≤0.1, INP ≤200 ms on mobile profile |

---

## 11. Error handling and resilience

- **Error boundaries:** one at the router root (full-page fallback with reload) and one per `AppLayout` outlet (keeps navigation usable). Boundaries never render stack traces.
- **Offline:** `navigator.onLine` banner; queries keep cached data; mutations fail with a recoverable message.
- **Empty vs error:** a failed request never renders an empty state (prevents "you have no entries" when the API is down).
- **Stale data:** background refetch on focus; optimistic updates only for routine item toggles and affirmation favourites, with rollback on error.
- **Session expiry:** `401` triggers one silent session refresh; if it fails, redirect to login preserving `next`.
- **Long-running export:** polling with backoff; the page remains usable.

---

## 12. Security responsibilities of the frontend

The frontend is **not** an authorization boundary. It must still:

1. Never store tokens, journal content, or mood notes in `localStorage`/`sessionStorage`.
2. Never render user content with `dangerouslySetInnerHTML`.
3. Treat API-provided strings as text (React escaping is the default).
4. Not log request bodies; the error logger sends only `code`, `status`, `requestId`.
5. Not include private content in URLs or query strings.
6. Not put `download_url` tokens in `Referer`-generating links (`rel="noreferrer"`).
7. Clear the query cache on logout (`queryClient.clear()`).
8. Reject `next` redirects that are not same-origin absolute paths.
9. Never trust `response_verified` display logic alone — the badge is derived from the API field.
10. Not hide security-relevant state (e.g. "pending" must look pending).

---

## 13. Configuration

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `/api/v1` | API prefix (same origin in production) |
| `VITE_APP_NAME` | `HerSpace` | Document title |
| `VITE_ENABLE_DEVTOOLS` | `false` | React Query devtools in dev only |

No secrets exist in the frontend bundle. Nothing environment-specific beyond the API base URL.

---

## 14. Build and delivery

- `npm run build` → `frontend/dist/`.
- Production: nginx serves `dist/` and proxies `/api/` to Gunicorn on the same origin (cookie sessions, no CORS).
- `index.html` gets `Cache-Control: no-cache`; hashed assets get `immutable, max-age=31536000`.
- SPA fallback: unknown non-`/api` paths return `index.html` (404 route handled client-side).
- CSP is set by Django/nginx, not by meta tags (see `security.md` §9.1). The inline theme script is allowed by hash.
- Source maps are generated but **not** served publicly in production.

---

## 15. Testing strategy (frontend)

| Level | Tool | Coverage target |
|---|---|---|
| Unit (hooks, utils, schemas) | Vitest | 90% of `hooks/` and `services/` |
| Component (ui primitives) | Testing Library + jest-axe | every `ui/` component |
| Page integration | Testing Library + MSW | happy path + one error path per page |
| E2E | Playwright | 12 critical journeys (`roadmap.md` §5) |
| Visual/responsive | Playwright screenshots at 320/768/1280 | key screens |
| Accessibility | jest-axe + manual keyboard pass | every page |

MSW handlers are generated from `docs/openapi.yaml` examples to keep mocks honest.

---

## 16. Known limitations (v1)

1. No SSR: unauthenticated users see a loading shell briefly; SEO is irrelevant for a private app but the welcome page is still indexable via static meta tags.
2. No offline write queue; offline edits are blocked with a clear message.
3. No websockets: notification badge polls every 60 s.
4. No virtualized lists; pagination caps at 100 items per page.
5. Charts are SVG and limited to ~400 points; longer ranges aggregate by day/week.
6. JavaScript is required (NFR-COMP-04).
