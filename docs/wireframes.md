# HerSpace — Wireframes, Layout and Design System

| Field | Value |
|---|---|
| Document ID | HS-UX-001 |
| Version | 1.0 |
| Date | 2026-10-31 |
| Traces to | `requirements.md` §6, `user-stories.md`, `api-documentation.md` |
| Consumed by | `frontend-architecture.md`, `roadmap.md` |

Wireframes are structural, not pixel-perfect. Each screen lists: route, purpose, layout, content blocks, states (loading / empty / error), interactions, and accessibility notes. Component names match `frontend-architecture.md` §7.

---

## 1. Design principles applied to layout

1. **One primary action per screen.** Everything else is secondary or tertiary.
2. **Calm density.** Maximum content width 1120 px; text columns max 68 characters.
3. **No red for feelings.** Mood and routine states never use error colour; only destructive confirmations do.
4. **Quiet navigation.** The sidebar never shows counts except unread notifications.
5. **Nothing is a streak.** Counts are always "in the last 7/30 days".
6. **Privacy by default in lists.** Journal lists show titles, never content previews.
7. **Every empty state offers exactly one next step.**

---

## 2. Design tokens

### 2.1 Colour

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | `#F8F7F4` | `#17181D` | Page background |
| `--surface` | `#FFFFFF` | `#21232B` | Cards, sheets |
| `--surface-alt` | `#EAE6F1` | `#2A2C36` | Selected nav, soft panels |
| `--surface-sage` | `#D8E5DF` | `#24312C` | Calm/wellness accents |
| `--surface-violet` | `#C7B8D8` | `#322B3D` | Highlights, chart accent |
| `--text` | `#323440` | `#ECEBE7` | Primary text |
| `--text-muted` | `#5A5D6C` | `#A8A9B4` | Secondary text |
| `--text-faint` | `#646776` | `#9294A0` | Timestamps, hints |
| `--border` | `rgba(50,52,64,0.10)` | `rgba(236,235,231,0.12)` | Dividers, inputs |
| `--focus` | `#6F5B8E` | `#B9A9D6` | Focus ring (3 px, 2 px offset) |
| `--accent` | `#7A6A96` | `#B9A9D6` | Primary buttons, links |
| `--accent-contrast` | `#FFFFFF` | `#1B1C22` | Text on accent |
| `--danger` | `#8C4A4A` | `#D79A9A` | Destructive only |
| `--success` | `#4F7A67` | `#8FBCA8` | Confirmation only |
| `--warning` | `#8A6A3B` | `#D6B583` | Caution copy |

Contrast targets: `--text` on `--bg` ≥ 11:1; `--text-muted` and `--text-faint` on `--bg`, `--surface`, and `--surface-alt` ≥ 4.5:1; `--accent` on `--surface` ≥ 4.5:1. Semantic text colours (`--accent`, `--danger`, `--success`, `--warning`) are only used for text/icons on `--bg` or `--surface`; on tinted surfaces, body text uses `--text` and links are underlined. Verified in CI with a token-contrast test.

### 2.2 Intensity ramp (mood)

Deliberately **not** red-to-green (which implies good/bad). A violet→sage ramp with the numeric value always shown:

| Intensity | Colour | Note |
|---|---|---|
| 1–2 | `#8B879B` | muted violet-grey |
| 3–4 | `#9E97AE` | |
| 5–6 | `#ADA9BC` | neutral midpoint |
| 7–8 | `#A9BFB3` | |
| 9–10 | `#86A997` | sage |

Each cell/segment also carries `aria-label="intensity 6 of 10"` and a visible number in detail views. The ramp is documented in the design README so charts and calendar stay consistent.

### 2.3 Type, spacing, shape

| Token | Value |
|---|---|
| Font heading | Manrope 500/600, self-hosted `woff2` |
| Font body | Inter 400/500, self-hosted `woff2` |
| `--text-display` | 32 px / 40 px (mobile 28/36) |
| `--text-h1` | 28 px / 36 px |
| `--text-h2` | 22 px / 30 px |
| `--text-h3` | 18 px / 26 px |
| `--text-body` | 16 px / 26 px |
| `--text-small` | 14 px / 22 px |
| `--text-micro` | 12 px / 18 px |
| Spacing scale | 4, 8, 12, 16, 24, 32, 48, 64 |
| Radius | 8 (inputs), 12 (buttons), 20 (cards), 28 (sheets/modals) |
| Shadow sm | `0 1px 2px rgba(50,52,64,.06)` |
| Shadow md | `0 8px 24px rgba(50,52,64,.08)` |
| Motion | 160 ms ease-out for fades, 220 ms for sheets; disabled under reduced motion |

### 2.4 Breakpoints and navigation

| Viewport | Navigation | Content |
|---|---|---|
| ≥1024 px | Fixed 248 px sidebar + top bar | Max 1120 px, 12-col grid, 24 px gutter |
| 640–1023 px | Collapsible icon rail (72 px), expandable overlay | Single column, 20 px gutter |
| ≤639 px | Bottom nav (5 items) + "More" sheet | Single column, 16 px gutter, 44 px targets |

Bottom nav: **Today**, **Mood**, **Journal**, **People**, **More**.
Sidebar order: Today, Mood, Journal, Self-care, People, Calm, Insights, then Settings at the bottom.

---

## 3. Shared shell

### 3.1 Desktop app shell

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  HerSpace                                            [Search]   [Bell 3] [Me]│  ← top bar 64px
├───────────────┬──────────────────────────────────────────────────────────────┤
│  Today        │  Good evening, Mira                          Fri, 31 October  │
│  Mood         │  ┌────────────────────────────────────────────────────────┐  │
│  Journal      │  │  How are you feeling today?                            │  │
│  Self-care    │  │  [ emotion chips ]                                     │  │
│  People       │  │  intensity 1 ─────●───── 10     [ Check in ]           │  │
│  Calm         │  └────────────────────────────────────────────────────────┘  │
│  Insights     │  ┌──────────────────────┐  ┌──────────────────────────────┐  │
│               │  │ I need someone       │  │ Today's routines             │  │
│               │  │ 3 people you trust   │  │ ○ Drink water                │  │
│               │  │ [ Ask for support ]  │  │ ○ Skincare                   │  │
│               │  └──────────────────────┘  └──────────────────────────────┘  │
│               │  ┌────────────────────────────────────────────────────────┐  │
│  ⚙ Settings   │  │ Last journal entry — 30 Oct · "A quieter evening"      │  │
└───────────────┴──┴────────────────────────────────────────────────────────┴──┘
```

**Top bar:** page title (mobile only), global search (journal + moods, opens ⌘K palette), notification bell with unread count, avatar menu (Profile, Settings, Log out).
**Sidebar:** active item uses `--surface-alt` with a 3 px left accent; icons 20 px, labels 15 px; collapsed rail shows tooltips.

### 3.2 Mobile shell

```
┌──────────────────────────────┐
│ HerSpace            [Bell 3] │
│                              │
│  Good evening, Mira          │
│  ┌────────────────────────┐  │
│  │ How are you feeling?   │  │
│  │ [chips]                │  │
│  │ ●──────────            │  │
│  │ [ Check in ]           │  │
│  └────────────────────────┘  │
│  ┌────────────────────────┐  │
│  │ I need someone         │  │
│  └────────────────────────┘  │
│                              │
├──────────────────────────────┤
│ Today  Mood  Journal  People │
│            More              │
└──────────────────────────────┘
```

`More` opens a bottom sheet: Self-care, Calm, Insights, Settings, Support resources, Log out.

### 3.3 Shared states

| State | Pattern |
|---|---|
| Loading | Skeleton blocks matching final layout; no spinners for content |
| Empty | Illustration-free, one sentence + one primary action |
| Error | Inline panel with a plain explanation and "Try again"; never a raw code |
| Offline | Top banner "You're offline. Changes aren't saved." |
| Success | Inline `aria-live="polite"` message that fades after 4 s; no toast stacks |

---

## 4. Authentication pages

### 4.1 `/` — Welcome
```
┌────────────────────────────────────────────────────────────┐
│  HerSpace                                       [Log in]   │
│                                                            │
│        A private space for how you actually feel.          │
│        Check in with yourself. Write what's true.          │
│        Reach the people who know you.                      │
│                                                            │
│        [ Create your space ]      [ I already have one ]   │
│                                                            │
│        ── no feeds, no strangers, no AI companion ──       │
│                                                            │
│  Privacy · Terms · Support resources                       │
└────────────────────────────────────────────────────────────┘
```
Centred, max 640 px text column, sage-tinted background wash, no stock imagery. Mobile stacks CTAs full-width.

### 4.2 `/register`
Two-column on desktop (form 480 px, quiet panel right), single column mobile.
```
Create your space
Email            [________________________]
Password         [________________________]  (strength hint, not a meter)
                 ✓ 12 characters  ✓ not a common password
[x] I agree to the Terms of Service (v1.0)
[x] I have read the Privacy Policy (v1.0)
[ Create account ]
Already have one? Log in
```
- Errors appear under the field, `aria-describedby`, `aria-invalid`.
- Submit disabled only while pending; never disabled for "invalid" (avoid mystery).
- On success → "Check your inbox" screen with the masked email and a resend link.

### 4.3 `/login`
```
Welcome back
Email     [__________________]
Password  [__________________]  [Forgot password?]
[ Log in ]
New here? Create your space
```
Generic error copy: "That email and password don't match." (no field-level hint which was wrong).
Locked: "Too many attempts. Try again in 12 minutes." with countdown, no input clearing.

### 4.4 `/forgot-password`
Single field + "Send a reset link". Always shows the same confirmation panel.

### 4.5 `/reset-password/:token`
New password + confirm, same policy hints. Expired state: "This link has expired. Request a new one." (no form).

### 4.6 `/verify-email/:token`
Three states: verifying (skeleton), success (auto-redirect to onboarding after 1.2 s with a manual link), failure (expired/used with resend action).

### 4.7 Email verification gate (in-app)
A non-dismissible inline banner on every app page for unverified users:
```
Verify your email to unlock your journal.  [Resend link]   (sent 2 min ago)
```
Private modules render a locked panel instead of data.

### 4.8 `/confirm-email-change/:token`
Three states: confirming (skeleton), success ("Your email is updated" + current address, manual link to settings), failure (expired/used with a "Request a new link in Settings" action). The old address keeps working until this succeeds.

---

## 5. Onboarding (`/onboarding/*`)

Shared layout: centred 560 px column, step indicator `1 of 5` as text + 5 dots, "Skip for now" on steps 1–4, "Back" always available.

### 5.1 `/onboarding/profile`
```
Let's set up your space
What should we call you?     [ Mira            ]
Time zone                    [ Europe/Berlin ▾ ]  (detected)
Pronouns (optional)          [ she/her         ]
A line about you (optional)  [                 ]  0/280
[ Continue ]
```

### 5.2 `/onboarding/wellness`
```
How would you like this space to feel?
Week starts on        ( Mon ) ( Sun )
Daily check-in reminder   [toggle]  time [ 20:00 ]
Calm Space default length [ 5 minutes ▾ ]
[ Continue ]
```

### 5.3 `/onboarding/notifications`
```
When should we reach you?
In-app notifications      [toggle on]
Email notifications       [toggle on]
Support request updates   [toggle on]
Quiet hours               [toggle]  from [22:00] to [07:00]
[ Continue ]
```
Quiet-hours explanation: "Nothing non-urgent will arrive during these hours."

### 5.4 `/onboarding/people`
```
Is there someone you trust?
Adding someone is optional. You can do this any time.
Name          [________________]
Relationship  [________________]
Email         [________________]
[ Add person ]      [ Skip for now ]
```
No invitation is sent here. After adding, a note: "You can invite them whenever you're ready."

### 5.5 `/onboarding/privacy`
```
What stays private
• Your journal and moods are yours. Nothing is shared automatically.
• A support request shares only what you tick, once, and you can withdraw it.
• You can export or delete everything from Settings.
• HerSpace doesn't diagnose anything and isn't a replacement for care.
[x] I understand
[ Enter my space ]
```

---

## 6. Dashboard `/app`

### 6.1 Desktop
```
Good evening, Mira                                     Fri, 31 Oct
┌───────────────────────────────────┐ ┌───────────────────────────────┐
│ How are you feeling today?        │ │ I need someone                │
│ [happy] [anxious] [tired] …       │ │ 3 people you trust            │
│ intensity 1 ──●────── 10          │ │ [ Ask for support ]           │
│ [ Check in ]   (saved → Edit)     │ │                               │
└───────────────────────────────────┘ └───────────────────────────────┘
┌───────────────────────────────────┐ ┌───────────────────────────────┐
│ Today's routines      2 of 5      │ │ This week                     │
│ ○ Drink water                     │ │ 4 check-ins · 2 entries       │
│ ○ Skincare                        │ │ [ See insights ]              │
│ ○ Breakfast                       │ │                               │
│ [ Open routines ]                 │ │                               │
└───────────────────────────────────┘ └───────────────────────────────┘
┌───────────────────────────────────────────────────────────────────┐
│ Last journal entry · 30 Oct · "A quieter evening"   [ Open ]      │
└───────────────────────────────────────────────────────────────────┘
```
- Greeting time-of-day is computed in the profile timezone.
- Suggestion card appears only when a suggestion is enabled and not dismissed; one at a time.
- No streaks, no "days in a row", no red.

### 6.2 Mobile
Cards stack in this order: check-in → I need someone → routines → week summary → last entry. Bottom nav visible.

### 6.3 States
| State | Behaviour |
|---|---|
| No check-in yet | Check-in card is expanded with emotion chips |
| Already checked in | Card shows saved summary + "Edit today's check-in" |
| No contacts | People card becomes "Add someone you trust" with a single CTA |
| Unverified | Locked panels + verify banner |
| Deletion scheduled | Redirect to `/app/settings/delete` status screen |

---

## 7. Emotional wellness

### 7.1 `/app/mood/check-in`
```
← Mood
How are you feeling today?                        Fri, 31 Oct
Emotions (choose any)
  Pleasant:   [happy] [peaceful] [grateful] [excited] [hopeful]
  Unpleasant: [sad] [anxious] [lonely] [angry] [overwhelmed] [tired]
  Neutral:    [numb]
Intensity
  1 ──────────●────────── 10        "6 · noticeable"
Note (optional)
  ┌──────────────────────────────────────────────┐
  │                                              │ 0/2000
  └──────────────────────────────────────────────┘
What was around you? (optional)
  [lack of sleep ×] [work ×]  [+ Add a trigger]
[ Save check-in ]        [ Cancel ]
```
- Chips toggle with `aria-pressed`; max 12 with a counter.
- Intensity is a native range input with keyboard support, plus number display.
- Trigger add opens a small popover with existing triggers and an inline "create" field.
- Save is upsert; on success navigate to `/app/mood` with an inline confirmation.

### 7.2 `/app/mood` — history
```
Mood                                        [ Check in today ]
[ All ] [ This month ] [ Last 30 days ]      filter: [emotion ▾]
──────────────────────────────────────────────────────────────
31 Oct   ● 6   anxious · grateful          "Busy day, but…"   →
30 Oct   ● 7   peaceful                    —                  →
28 Oct   ● 4   tired · overwhelmed         —                  →
──────────────────────────────────────────────────────────────
Showing 1–20 of 45                       [ Load more ]
```
Rows are buttons with an accessible name including date, intensity, emotions. No content preview of notes in the list (privacy); the note indicator is a dot.

### 7.3 `/app/mood/calendar`
```
October 2026                    [ ‹ ]  [ Today ]  [ › ]
Mo  Tu  We  Th  Fr  Sa  Su
         1   2   3   4   5
 6   7   8   9  10  11  12
13  14  15  16  17  18  19
20  21  22  23  24  25  26
27  28  29  30  31
Legend: ● recorded (violet→sage ramp)   ○ no check-in
Summary: 18 check-ins · average 5.7 · anxious most often (7)
```
- Grid is a `role="grid"` with arrow-key navigation; each cell is a button.
- Empty cells are `--surface` with a dashed border at 40% opacity; no warning colour.
- Selecting a day opens a side panel (desktop) or bottom sheet (mobile) with the entry.

### 7.4 `/app/mood/:id` — detail
Header (date, intensity, emotions), note block, triggers, "Shared in 1 request" with a link, Edit / Delete. Delete opens `ConfirmDialog` requiring the word `DELETE`.

### 7.5 Insights within Mood
`/app/mood` shows a compact weekly strip (7 dots + count) that links to `/app/insights/weekly`.

---

## 8. Human connection

### 8.1 `/app/people`
```
People you trust                          [ Add someone ]
────────────────────────────────────────────────────────
★ Alex Rivera        sister · email · Active        [Ask] →
  Sam Okafor         friend · WhatsApp · Invited    [Ask] →
  Priya Nair         therapist · email · Declined         →
────────────────────────────────────────────────────────
Invitations: 1 pending · [ View invitations ]
```
- Status pill colours: active = sage, invited = violet outline, declined/revoked = neutral grey (never red).
- `Ask` is disabled with a tooltip for `declined`/`revoked`.
- Empty state: "The people here are the ones you'd actually message. Add one person you trust." + CTA.

### 8.2 `/app/people/new` and `/app/people/:id/edit`
```
Add someone you trust
Name              [__________________________]
Relationship      [__________________________]  (e.g. sister, friend)
Email             [__________________________]
Phone             [__________________________]
Preferred channel ( Email ) ( WhatsApp ) ( SMS ) ( None )
Note to self      [__________________________]  0/280
[ Save ]   [ Cancel ]
```
Inline help: "We only contact them if you send an invitation or a support request."

### 8.3 `/app/people/:id`
Profile summary, status timeline (added → invited → accepted), private note, support history (last 5), actions: Invite / Resend / Revoke, Edit, Delete.
Delete dialog: "This removes Alex from your people. Your past support requests will keep their name."

### 8.4 `/app/invitations`
Table/list of invitations with contact, channel, sent, expires, status, actions (Resend, Revoke, Copy link when `manual_link`). Expired rows are muted with a "Send a new invitation" action.

### 8.5 `/app/support/new`
```
I need someone
Who would you like to reach?
  ( ) Alex Rivera      sister · email · Active   ★
  ( ) Sam Okafor       friend · WhatsApp · Invited  ⚠ not yet accepted
What kind of support?
  [ Talk ] [ Advice ] [ Company ] [ Listen ] [ Lonely ] [ Difficult day ]
Message (optional)
  ┌────────────────────────────────────────────┐
  │                                            │ 0/1000
  └────────────────────────────────────────────┘
Share something? (optional)
  [ ] Today's check-in            (preview)
      [ ] include my note
  [ ] A journal entry             [ choose… ]
  [x] I understand they may not be available, and this shares only what I tick.
[ Send request ]
```
- The consent checkbox is required only when a share is selected, and the API enforces it.
- Support-type tiles are single-select with `aria-pressed`.
- Warning for `invited` contacts is amber text, not blocking.

### 8.6 `/app/support` — history
```
Support requests                       [ Ask for support ]
[ All ] [ Waiting ] [ Answered ]
──────────────────────────────────────────────────────────
31 Oct  Alex Rivera   Listen      Waiting · expires in 2d  →
29 Oct  Sam Okafor    Company     Accepted · 12 min later   →
27 Oct  Alex Rivera   Talk        Expired                   →
```
Status is text + icon, never colour-only.

### 8.7 `/app/support/:id`
```
Listen · Alex Rivera
Sent 31 Oct, 21:40 · Expires 3 Nov, 21:40
Status: Waiting for a response
  "Waiting" means the request was sent. It doesn't mean Alex has seen it.
Message: "I don't need solutions…"
Shared: Today's check-in (intensity 6, anxious, grateful)  [ Withdraw ]
──────────────────────────────────────────────────────────
[ Send to someone else ]   [ Cancel request ]
```
Accepted state shows the response note + "via link" badge and "Withdraw share" if still shared.
Expired/declined state shows the alternatives block:
```
No response this time.
Other people you trust: [Sam] [Priya]
Support resources: [Find urgent support →]
```
Never "they didn't care" or "try again harder".

### 8.8 `/invitation/:token` (public)
```
Mira would like you to be someone she trusts.
Being a trusted contact means she may ask you for support in a hard moment.
You can decline, and you can ask her to remove you at any time.
[ Accept ]   [ Decline ]
This link expires on 27 October.
```
No owner email, no mood/journal content, no account creation. Decline asks for an optional note (≤280).

### 8.9 `/support-response/:token` (public)
```
Mira is asking for support
"I just want someone to listen"
" I don't need solutions, I just want to say it out loud. "
Shared with you: Check-in · 31 Oct · intensity 6 · anxious, grateful
[ I'm here ]   [ I can't right now ]
Optional note (they'll see this): [____________________]
```
After responding: "Thanks for letting her know." Link becomes inert.
If a share was withdrawn after the request was sent, its block reads "This was withdrawn by the sender" and shows no content; other active shares remain visible.

---

## 9. Journal

### 9.1 `/app/journal`
```
Journal                                [ New entry ]
[ All ] [ Daily ] [ Gratitude ] [ Memories ] [ Difficult ] [ Reflections ]
Search [____________________]   Tags: [evening ×] [work ×]
────────────────────────────────────────────────────────────────
30 Oct  A quieter evening        reflection  214 words  #evening   →
28 Oct  Three good things        gratitude    96 words            →
26 Oct  Hard morning             difficult   310 words  #work      →
────────────────────────────────────────────────────────────────
```
No content preview. `Search` debounced 300 ms, results show snippets only while searching (with a privacy hint: "Snippets show matching text").

### 9.2 `/app/journal/new` and `/app/journal/:id/edit`
```
← Journal
Title    [__________________________________________]
Date     [ 31 Oct 2026 ]   Category [ Daily ▾ ]
Tags     [evening ×] [ + add ]
┌──────────────────────────────────────────────────────────────┐
│ Write freely…                                                │
│                                                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                                   1,204 characters · 214 words
[ Save entry ]   [ Cancel ]
Unsaved changes warning on navigation.
```
Distraction-free: sidebar collapses on desktop while typing (optional toggle), no autosave (explicit save), draft preserved in memory only.

### 9.3 `/app/journal/:id`
Reading layout, max 68 characters per line, serif-optional body (Inter kept for consistency), metadata row, tags, linked check-in chip, prompt reference, Edit / Delete. Delete requires typing the title.

### 9.4 `/app/journal/gratitude`
```
Gratitude
Three small things, if you feel like it.
[ Today's entry: "Three good things" → ]
This month: 6 entries
──────────────────────────────
30 Oct  Three good things   →
24 Oct  Sunlight            →
```
Quick add: one title field + content, category fixed to `gratitude`.

### 9.5 `/app/journal/prompts`
Prompt cards grouped by category with a "Use this prompt" action that opens the editor with `prompt_id` and a prefilled title. Prompts are questions, never instructions.

---

## 10. Self-care

### 10.1 `/app/selfcare`
```
Self-care                                    [ New routine ]
Today · Friday 31 October
┌──────────────────────────────────────────────────────────┐
│ Slow morning            2 of 5     [ Continue ]          │
│ ✓ Drink water  ○ Skincare  ○ Breakfast  ○ …              │
└──────────────────────────────────────────────────────────┘
Not scheduled today
  Evening wind-down — "Not scheduled for Friday"
This week: 4 completions · [ History ]
```
No streak, no percentage-shaming copy. Progress ring is decorative with a text equivalent.

### 10.2 `/app/selfcare/new` and `/app/selfcare/:id/edit`
```
New routine
Name            [ Slow morning            ]
Time of day     ( Morning ) ( Afternoon ) ( Evening ) ( Anytime )
Days            [M][T][W][T][F][ ][ ]     (toggle chips)
Reminder        [toggle]  [ 07:30 ]
Steps
  1  [ Drink water            ]  optional [ ]  ~1 min  [⋮]
  2  [ Skincare               ]  optional [x]  ~5 min  [⋮]
  + Add a step
[ Save routine ]   [ Cancel ]
```
Reorder via drag handle **and** keyboard (Alt+↑/↓), with an `aria-live` announcement.

### 10.3 `/app/selfcare/:id`
Routine summary, today's checklist, last 30 days as a quiet grid of small squares (filled = completed, outline = not scheduled, empty = no entry), edit/deactivate/delete.

### 10.4 `/app/selfcare/history`
Date-range picker (default 30 days), routine filter, list of completions with items completed/total. Missing days are simply absent from the list; a footnote explains "Days without an entry are not counted as missed."

---

## 11. Calm Space

### 11.1 `/app/calm`
```
Calm Space
[ Breathe ]  [ Ground ]  [ Meditate ]  [ Affirmations ]
┌────────────────────────────┐ ┌────────────────────────────┐
│ Box breathing              │ │ 5-4-3-2-1 grounding        │
│ 4-4-4-4 · 8 cycles · 4 min │ │ About 3 minutes            │
│ [ Begin ]                  │ │ [ Begin ]                  │
└────────────────────────────┘ └────────────────────────────┘
If you need a person right now: [ Support resources ]
```

### 11.2 `/app/calm/breathing/:slug`
```
        Box breathing
        ┌──────────────────┐
        │                  │
        │      Inhale      │      ← circle scales with phase
        │        4         │
        └──────────────────┘
        Cycle 3 of 8
        [ Pause ]   [ End ]
        Sound [toggle]   Reduced motion respected
```
Reduced motion: static ring with a numeric countdown and phase label.

### 11.3 `/app/calm/grounding`
Step card with progress `2 of 5`, Back / Next, "5 things you can see" + a short prompt. Exit asks "Save this session or discard?".

### 11.4 `/app/calm/meditation`
Duration chips (3/5/10/20 min) → timer with pause, soft chime toggle, and "End early" (saves a partial session).

### 11.5 `/app/calm/affirmations`
```
Affirmations                     [ Favourites ]
[ General ] [ Self-compassion ] [ Boundaries ]
┌──────────────────────────────────────────┐
│ "I can take up space without apologising."│  ☆
└──────────────────────────────────────────┘
```
Card deck with Prev/Next, no auto-advance.

---

## 12. Insights

### 12.1 `/app/insights`
Hub with three cards: This week, This month, Activity overview. Each shows 2 numbers and a link.

### 12.2 `/app/insights/weekly`
```
This week · 26 Oct – 1 Nov            [ ‹ ] [ This week ] [ › ]
5 check-ins · average intensity 5.6
┌───────────────────────────────────────────────────────┐
│ Mood through the week                                  │
│ 10 ┤        ●                                          │
│  5 ┤  ●  ●     ●  ●                                   │
│  1 ┤                                                   │
│    Mo Tu We Th Fr Sa Su                                │
└───────────────────────────────────────────────────────┘
Top emotions   anxious 3 · grateful 2 · tired 2
Journal        3 entries
Routines       4 of 5 scheduled days
Calm           24 minutes
What this shows
• You recorded anxious 3 times this week.
• You completed Slow morning 4 times.
These are observations from your records, not medical advice.
[ View as table ]
```
Chart has a table alternative and a text summary. No trend arrows unless ≥3 data points and even then descriptive only.

### 12.3 `/app/insights/monthly`
Same structure + comparison block:
```
Check-ins   12 this month · 8 last month
Journal      9 this month · 11 last month
```
Neutral phrasing, no "improved/worsened".

### 12.4 Insufficient data
```
Not enough data yet
A few more check-ins will make this meaningful.
[ Check in today ]
```
No empty chart axes.

---

## 13. Notifications

### 13.1 `/app/notifications`
```
Notifications                     [ Mark all read ]
[ All ] [ Unread ]
──────────────────────────────────────────────
● Alex responded           2h ago   Support request →
  Your request from 31 Oct has a response.
○ Export ready             1d ago   Download →
○ New login                3d ago   Security →
```
Bodies are template text only; no private content. Clicking marks read and navigates.

---

## 14. Settings

Shared layout: left sub-nav (desktop) / stacked list (mobile), content max 720 px.

### 14.1 `/app/settings/profile`
Display name, pronouns, bio, date of birth (optional), timezone, locale (read-only "English"), email (with "Change email" flow), save bar.

### 14.2 `/app/settings/security`
Change password form, active sessions summary ("Logged in on this device"), "Log out everywhere", email verification status.

### 14.3 `/app/settings/privacy`
```
Privacy & consent
What you've agreed to
  Terms of Service v1.0        Granted 20 Oct 2026
  Privacy Policy v1.0          Granted 20 Oct 2026
  Wellness disclaimer          Granted 21 Oct 2026
  Email notifications          Revoked 25 Oct 2026   [ Grant ]
Sharing
  Active shares: 1   [ Review ]
[ Read the privacy information → ]
```

### 14.4 `/app/settings/notifications`
Toggles for in-app/email/support updates, quiet hours, per-category table. Security alerts noted as always-on.

### 14.5 `/app/settings/data`
```
Your data
[ Request an export ]
  Latest: ready · 2.1 MB · expires in 5 days   [ Download ]
  Exports are deleted after 7 days.
[ Read what's included ]
```
Progress states: queued → building → ready → expired.

### 14.6 `/app/settings/delete`
```
Delete your account
This removes your journal, moods, routines, contacts, and support history.
It cannot be undone after 7 days.
Password        [________________]
Type DELETE     [________________]
[ Schedule deletion ]   (disabled until both match)
```
After scheduling: status panel with the date, "Cancel deletion" (if this restricted session remains), and a note that a cancellation link was emailed.

### 14.7 `/app/settings/people`
Redirects to `/app/people` (single source of truth).

---

## 15. Public pages

### 15.1 `/privacy` and `/terms`
Long-form reading layout, 68-character measure, sticky table of contents on desktop, version + effective date at top. Content mirrors `security.md` §10 and the retention table.

### 15.2 `/support-resources`
```
Support right now
If you are in immediate danger, contact your local emergency number.
Region [ Global ▾ ]
Crisis lines
  Name · phone · SMS · website
Listening services
  …
[ Back to HerSpace ]
```
No login required; reachable from Calm, Insights, support flows, and the footer.

### 15.3 `/404`
" This page isn't here. It may have been removed, or the link may be old." + links to Today, Journal, Support resources.

---

## 16. Component inventory (used by `frontend-architecture.md`)

| Component | Variants | Notes |
|---|---|---|
| `AppShell` | desktop, rail, mobile | Skip link, landmarks |
| `SidebarNav` / `BottomNav` / `MoreSheet` | — | Focus management |
| `TopBar` | — | Search trigger, bell, avatar |
| `PageHeader` | with/without actions | One `h1` |
| `Card` | default, sage, violet, interactive | Radius 20 |
| `Button` | primary, secondary, ghost, danger, icon | Loading state, 44 px min |
| `TextField` / `TextArea` | with counter, error, hint | `aria-describedby` wiring |
| `Select` / `Combobox` | native-first | Custom only when needed |
| `Toggle` | — | `role="switch"` |
| `ChipGroup` | single, multi | `aria-pressed` |
| `Slider` | intensity | Native range + numeric output |
| `StatusPill` | active, invited, pending, accepted, declined, expired | Text + icon, never colour-only |
| `EmptyState` | — | One action |
| `Skeleton` | text, card, chart | Reduced-motion safe |
| `InlineAlert` | info, caution, error | Not a toast |
| `ConfirmDialog` | typed-confirmation variant | Focus trap, Escape |
| `Sheet` | mobile modal | Drag handle, focus trap |
| `Tabs` | underline | Arrow-key roving tabindex |
| `CalendarGrid` | month | `role="grid"` |
| `LineChart` / `BarChart` | — | Recharts wrapper + table fallback |
| `ProgressRing` | — | Decorative, text alternative |
| `BreathePacer` | animated, static | Respects reduced motion |
| `NotificationItem` | unread/read | |
| `Toast` | success, error | Single at a time, `aria-live` |
| `SupportResourceList` | — | External links `rel="noopener noreferrer"` |

---

## 17. Copy rules (enforced in review)

| Do | Don't |
|---|---|
| "No check-in for this day." | "You missed a day." |
| "Waiting for a response." | "Help is on the way." |
| "You completed this 4 times this week." | "4-day streak!" |
| "Not enough data yet." | "Your mood is declining." |
| "This shares only what you tick." | "We'll let them know how you feel." |
| "You can withdraw this." | "Shared forever." |
| "These are observations, not medical advice." | "This suggests depression." |
| "Someone you trust" | "Your support network is incomplete" |

A copy lint script checks the built bundle for banned phrases (`security.md` §13).

---

## 18. Accessibility checklist per screen

Every page must pass:

1. Exactly one `h1`; headings in order.
2. Landmarks: `header`, `nav`, `main`, `footer` (public pages).
3. Skip link as the first focusable element.
4. All interactive elements reachable and operable by keyboard.
5. Visible focus ring (`--focus`, 3 px, 2 px offset) on every control.
6. Form errors announced via `aria-live` and linked with `aria-describedby`.
7. Charts accompanied by a table or textual summary.
8. Status changes announced with `aria-live="polite"`.
9. Colour never the only carrier of meaning (status pills have text; intensity has numbers).
10. Modals/sheets trap focus and restore it on close.
11. Touch targets ≥ 44×44 px on mobile.
12. `prefers-reduced-motion` and the in-app setting both disable animation.
13. Zoom to 200% without loss of content or horizontal scrolling at 320 px.
14. Time-based content (breathing, timer) has pause controls and no forced timing.

---

## 19. Screen → route → API map

| Screen | Route | Primary endpoints |
|---|---|---|
| Welcome | `/` | — |
| Register | `/register` | `POST /auth/register/` |
| Login | `/login` | `POST /auth/login/`, `GET /auth/session/` |
| Forgot / reset | `/forgot-password`, `/reset-password/:token` | `POST /auth/password-reset/`, `POST /auth/password-reset/confirm/` |
| Verify | `/verify-email/:token` | `POST /auth/verify-email/` |
| Confirm email change | `/confirm-email-change/:token` | `POST /auth/email-change/confirm/` |
| Onboarding ×5 | `/onboarding/*` | `PATCH /profile/`, `PATCH /preferences/`, `POST /contacts/`, `POST /onboarding/complete/` |
| Dashboard | `/app` | `GET /moods/?local_date=`, `GET /routines/today/`, `GET /contacts/`, `GET /journal/?page_size=1`, `GET /notifications/unread-count/` |
| Check-in | `/app/mood/check-in` | `POST /moods/`, `GET /moods/emotions/`, `GET/POST /moods/triggers/` |
| Mood history | `/app/mood` | `GET /moods/` |
| Mood calendar | `/app/mood/calendar` | `GET /moods/calendar/` |
| Mood detail | `/app/mood/:id` | `GET/PATCH/DELETE /moods/{id}/` |
| People | `/app/people` | `GET /contacts/` |
| Add/edit person | `/app/people/new`, `/app/people/:id/edit` | `POST /contacts/`, `PATCH /contacts/{id}/` |
| Person detail | `/app/people/:id` | `GET/DELETE /contacts/{id}/`, `POST /contacts/{id}/invite/` |
| Invitations | `/app/invitations` | `GET /contacts/{id}/invitations/`, `POST /invitations/{id}/resend/`, `POST /invitations/{id}/revoke/` |
| Ask for support | `/app/support/new` | `GET /contacts/`, `POST /support-requests/` |
| Support history | `/app/support` | `GET /support-requests/` |
| Support detail | `/app/support/:id` | `GET /support-requests/{id}/`, `POST /support-requests/{id}/cancel/`, `DELETE /support-requests/{id}/shares/{shareId}/` |
| Journal list | `/app/journal` | `GET /journal/`, `GET /journal/tags/` |
| New/edit entry | `/app/journal/new`, `/app/journal/:id/edit` | `POST/PATCH /journal/`, `GET /journal/prompts/` |
| Entry detail | `/app/journal/:id` | `GET/DELETE /journal/{id}/` |
| Gratitude | `/app/journal/gratitude` | `GET /journal/?category=gratitude` |
| Prompts | `/app/journal/prompts` | `GET /journal/prompts/` |
| Self-care | `/app/selfcare` | `GET /routines/today/` |
| New/edit routine | `/app/selfcare/new`, `/app/selfcare/:id/edit` | `POST/PATCH /routines/`, `POST/PATCH/DELETE /routines/{id}/items/…` |
| Routine detail | `/app/selfcare/:id` | `GET /routines/{id}/`, `POST /routines/{id}/complete/` |
| Routine history | `/app/selfcare/history` | `GET /routines/completions/` |
| Calm | `/app/calm` | `GET /calm/activities/` |
| Breathing | `/app/calm/breathing/:slug` | `GET /calm/activities/{slug}/`, `POST /calm/sessions/` |
| Grounding | `/app/calm/grounding` | same |
| Meditation | `/app/calm/meditation` | same |
| Affirmations | `/app/calm/affirmations` | `GET /calm/affirmations/`, `POST/DELETE /calm/affirmations/{id}/favorite/` |
| Insights hub | `/app/insights` | `GET /insights/overview/` |
| Weekly / monthly | `/app/insights/weekly`, `/app/insights/monthly` | `GET /insights/weekly/`, `GET /insights/monthly/` |
| Notifications | `/app/notifications` | `GET /notifications/`, `PATCH`, `read-all` |
| Settings profile | `/app/settings/profile` | `GET/PATCH /profile/` |
| Settings security | `/app/settings/security` | `POST /auth/password-change/`, `POST /auth/logout-all/` |
| Settings privacy | `/app/settings/privacy` | `GET/POST /privacy/consents/` |
| Settings notifications | `/app/settings/notifications` | `GET/PATCH /preferences/` |
| Settings data | `/app/settings/data` | `GET/POST /privacy/export/`, `POST /privacy/export/{id}/download/`, `GET /privacy/export/{id}/download/?token=` |
| Settings delete | `/app/settings/delete` | `GET/POST /privacy/account-deletion/`, `POST /privacy/account-deletion/cancel/` |
| Invitation response | `/invitation/:token` | `GET/POST /public/invitations/{token}/*` |
| Support response | `/support-response/:token` | `GET/POST /public/support-requests/{token}/*` |
| Privacy / terms | `/privacy`, `/terms` | `GET /privacy/policies/` |
| Support resources | `/support-resources` | `GET /privacy/resources/` |
