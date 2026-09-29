# How the email system works

Servantium's system email is written once, here, and sent by Postmark. The product sends an email by naming a template and supplying its data. Product code never contains email HTML.

Three systems each do one job:

| System | Its job | What it holds |
|---|---|---|
| **GitHub** (this repo) | Where emails are written, reviewed and tested | The MDX masters, the components, the brand images, the field contract |
| **Postmark** | Where emails are stored and sent | The compiled templates, pushed from here; delivery, bounces, suppressions, unsubscribes |
| **Servantium** (the backend) | Decides who gets which email, and when | The events that trigger emails, and the code that sends a template by alias with its data |

## The path of a change

```
  edit src/emails/task.mdx
          │  pull request
          ▼
  ┌──────────────────────────────────────────────┐
  │ GitHub Actions: build + test                 │  the rendered gallery is attached to
  │ (masters → HTML, plain text, contract)       │  the run, so reviewers see every email
  └──────────────────────┬───────────────────────┘
                         │  merge to main
                         ▼
  ┌──────────────────────────────────────────────┐
  │ Postmark QA server                           │  engineering tests the real sends
  │ every template pushed, by alias              │
  └──────────────────────┬───────────────────────┘
                         │  tag email-vX.Y.Z
                         ▼
  ┌──────────────────────────────────────────────┐
  │ R2 (assets.servantium.com/brand)             │  brand images synced
  │ Postmark production server                   │  every template pushed, by alias
  └──────────────────────┬───────────────────────┘
                         │
                         ▼
  ┌──────────────────────────────────────────────┐
  │ Servantium backend                           │  POST /email/withTemplate
  │ TemplateAlias: "task"                        │  with the TemplateModel the
  │ TemplateModel: { actor_name, task_name, … }  │  contract describes
  └──────────────────────────────────────────────┘
```

The workflow is [`.github/workflows/email-templates.yml`](../../../.github/workflows/email-templates.yml). Its QA and production jobs stay off until engineering sets the repository variable `EMAIL_DEPLOY` to `on`, after the Postmark servers and secrets exist.

## What the build makes

`npm run build` reads every master in `src/emails/` and writes `dist/`:

| Output | For |
|---|---|
| `dist/postmark/<alias>/` | The template in the folder layout the Postmark CLI pushes: `content.html`, `content.txt`, `meta.json` |
| `dist/contract.json` | Every template's stream, sender, reply-to, subject and fields, with examples and notes |
| `dist/servantium_email_contract.py` | The same contract as Python `TypedDict`s, for the backend |
| `dist/index.html` | The gallery: every email with its examples, at desktop and phone width |
| `dist/stylesheet.html` | The style guide, rendered. Also written as [style-guide.md](./style-guide.md) |
| `dist/firebase/password-reset.html` | The reset email as a Firebase console template, while Firebase still sends resets |
| `dist/assets/` | The brand images, as they'll be uploaded to R2 |

The template file name is the Postmark alias: `task.mdx` becomes the template `task`. Aliases are how the backend names templates, so they don't change once engineering uses them.

## Inside a master

A master is one MDX file: frontmatter, then a body.

- **The frontmatter builds the frame.** The banner (label, one-line title, tone), the footer (why they got it) and the Postmark stream all come from it, and it's validated like a schema. It also declares the **fields**: every value the sender supplies.
- **The body is Markdown plus components.** A paragraph becomes `Text`, `##` becomes `Heading`, a list becomes a table Outlook can draw. Components like `DataTable`, `Button` and `Callout` need no import.
- **`{{ field }}` passes through untouched.** The build protects it from MDX, so it reaches Postmark as a merge tag, and Postmark fills it at send time.

The loader wraps every master in the same frame:

```
Email ─┬─ Banner    forest night sky, logo, label, one-line title, tone rule
       ├─ Body      white card: the master's content, closed by a strip of the same sky
       └─ Footer    links · why you got this + help@ · address + LinkedIn
```

Each component is one file in [`src/components/`](../src/components/), with a header comment saying what it's for and how to use it. [style-guide.md](./style-guide.md) is the full reference.

## Where facts come from

Nothing that appears in more than one email is typed into an email:

| Fact | Source | Changes reach |
|---|---|---|
| Colours, fonts | Verdant tokens (`packages/verdant`), synced by the build | the next release |
| Address, footer links, help@, LinkedIn | [`packages/brand/company.json`](../../brand/company.json) | the next release |
| Logo, banner art, icons | [`packages/brand/assets/`](../../brand/assets/), served from R2 | every email, including ones already sent |

Images load from `https://assets.servantium.com/brand/…` each time an email is opened. The addresses never change, so replacing an image updates every email ever sent. [Hosting](../../brand/docs/hosting.md) covers the bucket.

## The rules are tests

`npm test` checks every email twice, as previewed and as sent, plus every style-guide sample. It covers the design decisions (one banner, no coloured side bars, one primary button, one-line titles), what mail clients punish (Gmail's 102 KB clip, SVG, flex, missing Outlook button shapes), accessibility (every colour pair passes WCAG AA, alt text, a plain-text part), streams (unsubscribe on broadcast only) and the contract (every field declared, used and visible to Postmark). A broken rule fails the pull request, so a rule can only change by changing the test.

## Who does what

| | Design system | Engineering |
|---|---|---|
| Masters: copy, layout, components, rules | owns | reviews |
| Brand images and company facts | owns | |
| The field contract | proposes in the pull request | reviews and approves |
| R2 bucket and `assets.servantium.com` | sets up and owns | |
| Postmark: account, servers, streams, sender domain (DKIM, Return-Path), tokens | | owns |
| GitHub secrets and the `EMAIL_DEPLOY` switch | | owns |
| Sending: which event triggers which alias, with which data | | owns |
| Support inbound: help@ to a ticket, threading replies | | owns |
| Testing real sends in QA | | owns |
| Merging to main (QA) | either | either |
| Tagging a production release | agreed per release | agreed per release |

## Why it's built this way

- **One source.** An email exists once, in git. Postmark holds copies it's given. Edits made in Postmark's editor are overwritten on the next push.
- **The backend sends data, not HTML.** MDX is compiled at build time, never at send time: compiling evaluates code, which Cloudflare Workers forbid, and product code shouldn't render email anyway. The backend picks an alias and supplies fields.
- **Postmark-native.** Merge tags, optional sections and repeated rows are all Postmark's own Mustachio features, so there's no rendering service to run.
- **Plain HTML email.** Tables, inline styles, a VML button shape for Outlook, and images that degrade to a flat colour. Nothing depends on a client doing the modern thing.
