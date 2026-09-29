# @servantium/verdant-email

Every email Servantium's product sends, written once, here.

Each email is one MDX file in [`src/emails/`](./src/emails/). The build turns them into Postmark templates, a plain-text version of each, a data contract for engineering, and a preview gallery. A GitHub workflow pushes the templates to Postmark, and the product sends an email by naming it and supplying the data. Product code never contains email HTML.

```bash
npm run build                # compile every email → dist/ (and docs/style-guide.md)
npm test                     # the design, mail-client, accessibility and contract rules
open dist/index.html         # every email, at desktop and phone width
open dist/stylesheet.html    # the style guide, rendered
```

## Read next

| If you want to… | Read |
|---|---|
| Understand how GitHub, Postmark and Servantium fit together | [docs/how-it-works.md](./docs/how-it-works.md) |
| Write or change an email, with a worked example | [docs/writing-an-email.md](./docs/writing-an-email.md) |
| Choose, name and format the data an email needs | [docs/fields.md](./docs/fields.md) |
| Look up a component, a frontmatter key, a tone or a rule | [docs/style-guide.md](./docs/style-guide.md) |
| Release, add or retire a template; release notes; images | [docs/maintaining.md](./docs/maintaining.md) |
| Know where the images are hosted | [../brand/docs/hosting.md](../brand/docs/hosting.md) |

## The emails

The file name is the Postmark template alias.

| File | What it is | Stream |
|---|---|---|
| `welcome.mdx` | Someone was added to an existing organization. Carries the set-password link. | transactional |
| `welcome-organization.mdx` | A new organization was created; this is its first administrator. | transactional |
| `password-reset.mdx` | Forgot password. | transactional |
| `task.mdx` | Something happened to a task: assigned, commented, rescheduled, completed. | transactional |
| `notification.mdx` | Any other single event: approvals, status changes, publications. | transactional |
| `digest.mdx` | A daily or weekly summary of many events, for people who prefer one email. | transactional |
| `support-received.mdx` | The automatic first reply when a request reaches help@. | transactional |
| `support-reply.mdx` | Every message from our team on a request, with the conversation so far. | transactional |
| `incident.mdx` | A service disruption, and each status change. | transactional |
| `incident-resolved.mdx` | The disruption is over. | transactional |
| `maintenance.mdx` | Planned downtime, at least 72 hours ahead. | transactional |
| `release-notes.mdx` | What shipped this month. Rewritten monthly from the help site. | broadcast |
| `regulatory-notice.mdx` | A required notice under a customer's DPA or contract. Example only; legal review pending. | transactional |

## A master, in brief

```mdx
---
name: Task message
subject: "{{ actor_name }} {{ action }}: {{ task_name }}"
preheader: "Due {{ due }} · {{ engagement }}"
label: Task
title: Task update
stream: transactional
footer:
  reason: "Sent because you're on this task in {{ organization_name }}."
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

- **The frontmatter builds the frame:** banner, footer and stream. It's validated like a schema.
- **`fields` is the contract.** Every value the sender supplies is declared, with an example and, where the format matters, a note.
- **The body is Markdown plus components,** which need no import.
- **`{{ field }}` works anywhere** except the banner title, and reaches Postmark untouched.

## Layout

```
packages/verdant-email/
├── src/
│   ├── emails/          the masters: one .mdx per email, named for its Postmark alias
│   ├── components/      one file per component, each with a header saying how to use it
│   ├── mdx.tsx          the loader: frontmatter schema, field contract checks, MDX → components
│   ├── render.tsx       the HTML document shell (Outlook head, mobile rules, preheader)
│   ├── theme.ts         Verdant tokens mapped to email roles; the three tones
│   ├── stylesheet.ts    the style guide's content: samples, writing rules, tones, bans
│   └── text.ts          HTML → the plain-text version
├── scripts/             build (export.tsx), contract writers, release-notes drafter, Postmark validator
├── test/                the rules
└── docs/                how it works, writing an email, fields, the style guide, maintaining
```

## Before the first real send

These are outside this repo. Engineering owns everything except the R2 bucket.

- Create the R2 bucket `servantium-assets` on `assets.servantium.com` ([plan](../brand/docs/hosting.md)).
- Set up the Postmark servers, sender domain records and tokens; add the GitHub secrets; set the `EMAIL_DEPLOY` variable to `on`.
- Run `scripts/postmark-validate.mjs` once by hand against the QA server.
- Test real sends in Outlook desktop, Gmail and Apple Mail.
- Get legal review of the regulatory notice.
- When the status page exists, set `live: true` on the Status footer link in `packages/brand/company.json`.
