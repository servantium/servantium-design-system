# @servantium/verdant-email

Every email Servantium sends to its users, written once, here.

The master of each email is one MDX file in `src/emails/`. The build turns the masters into Postmark templates, a plain-text version of each, a data contract for engineering, and a preview gallery. A GitHub workflow pushes the templates to Postmark. The product then sends an email by naming it and supplying the data. Product code never contains email HTML.

```bash
npm run build          # compile every master → dist/
npm test               # the design, client-safety, accessibility and contract rules
open dist/index.html   # every email, at desktop and phone width
open dist/stylesheet.html   # the style guide: frontmatter, writing, tones, components, rules
```

## The masters

| File (= Postmark alias) | What it is | Stream |
|---|---|---|
| `welcome.mdx` | Someone was added to an existing workspace. Carries the set-password link. | transactional |
| `welcome-workspace.mdx` | A new workspace was created; this is its first administrator. | transactional |
| `password-reset.mdx` | Forgot password. | transactional |
| `task.mdx` | Something happened to a task: assigned, commented, rescheduled, completed. | transactional |
| `notification.mdx` | Any other single event: approvals, status changes, publications. | transactional |
| `digest.mdx` | A daily or weekly summary of many events, for people who prefer one email. | transactional |
| `support-ticket.mdx` | A help@ request was received, answered or resolved. | transactional |
| `incident.mdx` | A service disruption. | transactional |
| `incident-resolved.mdx` | The disruption is over. | transactional |
| `maintenance.mdx` | Planned downtime, at least 72 hours ahead. | transactional |
| `release-notes.mdx` | What shipped this month. Rewritten monthly. | broadcast |
| `regulatory-notice.mdx` | A required notice under a customer's DPA or contract. Example only; legal review pending. | transactional |

## Writing a master

```mdx
---
name: Task message
subject: "{{ actor_name }} {{ action }}: {{ task_name }}"
preheader: "Due {{ due }} · {{ engagement }}"
label: Task
title: "{{ actor_name }} {{ action }} a task"
subtitle: "{{ engagement }}"
stream: transactional
footer:
  reason: "You're receiving this because you're on this task in {{ workspace_name }}."
fields:
  actor_name: { example: Jules Hart, note: Who did it }
  message: { example: "Flag anything outside tolerance.", optional: true }
  …
---
<DataTable title="{{ task_name }}" rows={[["Due", <b>{"{{ due }}"}</b>]]} />

<If field="message">
  <Callout tone="neutral" title="What they wrote">“{{ . }}”</Callout>
</If>

<Button href="{{ task_url }}">Open task</Button>
```

- **The frontmatter builds the frame**: banner, footer and stream. It's validated like a schema.
- **`fields` is the contract.** Every value the sender supplies is declared here, with an example, and a note where it helps. A field can be a list of items, which a component repeats. The build fails if an email uses a field it doesn't declare, or declares one it never uses.
- **The body is Markdown plus the style-guide components.** Components need no import.
- **`{{ field }}` works anywhere**: in text, in a component prop, and in the frontmatter. It reaches Postmark untouched.
- **Optional content**: `<If field="x">` shows only when `x` is supplied; inside it, `{{ . }}` is its value. `<Editable field="x">default</Editable>` is copy the sender may replace. Postmark handles both natively.
- **Lists**: `<Updates field="items" />` renders one row per item. `<DataTable each="details" />` renders one table row per `{ label, value }`.

## What the build produces

| Output | For |
|---|---|
| `dist/postmark/<alias>/` | `content.html`, `content.txt` and `meta.json`: the folder layout the Postmark CLI pushes |
| `dist/contract.json` | Every template's stream, sender, reply-to and fields, with examples and notes |
| `dist/servantium_email_contract.py` | The same contract as Python `TypedDict`s, for the backend |
| `dist/index.html`, `dist/stylesheet.html` | The gallery and the style guide |
| `dist/firebase/password-reset.html` | The reset email as a Firebase console template, while Firebase still sends resets |

## Shipping

`.github/workflows/email-templates.yml` runs on changes to this package or `packages/brand`:

- **Pull request:** build and test. The gallery is attached to the run.
- **Merge to main:** sync the email images to R2 (`assets.servantium.com`), check every template against Postmark's own engine, then push them all to the Postmark QA server.
- **Tag `email-v*`:** the same steps against the Postmark production server.

Postmark is a deployment target only: edits made in its interface are overwritten on the next push. Templates deleted here must also be deleted in Postmark by hand.

## The rules

`npm test` checks every email, both the preview and the version that gets sent, plus every style-guide sample. It fails on any of these:

- **Design:** no coloured bar down the side of anything, one banner on every email, footer links and address from `company.json`, at most one primary button.
- **Mail clients:** over 102 KB (Gmail clips it), SVG, flex or grid layout, a button without its Outlook shape, an image without an absolute URL, or no plain-text version.
- **Accessibility:** every text colour pair and both button styles pass WCAG AA (4.5:1), every image has alt text, and tone marks are visible on the banner (3:1).
- **Streams:** broadcast mail carries Postmark's unsubscribe link; transactional mail never does.
- **Contract:** a field that's undeclared, declared but unused, or referenced where Postmark can't see it (inside a section or list).
- **Mascot:** none on attention or urgent mail (the mascot is off entirely for now).

## Before the first real send

- Create the R2 bucket `servantium-assets` on `assets.servantium.com`.
- Set up the Postmark servers, domain records and tokens (see the engineering brief).
- Run `scripts/postmark-validate.mjs` once by hand against the QA server.
- Test in Outlook desktop, Gmail and Apple Mail.
- Get legal review of the regulatory notice.
