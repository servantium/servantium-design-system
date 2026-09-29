# How the email system works

Servantium's system email is written once, here, and sent by Postmark. The product sends an email by naming a template and supplying its data. Product code never contains email HTML.

Grove Email sits in the design system beside the website's components:

| Layer | Package | For |
|---|---|---|
| Tokens | `@servantium/verdant` | Colours, type and spacing, for every surface |
| Components | `@servantium/grove` | The website and help center (Astro) |
| Components | `@servantium/grove-email` | Email: components, the emails built from them, the rules |
| Brand | `@servantium/brand` | Logos, the mascot, email art, icons and company facts, served from `assets.servantium.com` |

Three systems each do one job:

| System | Its job | What it holds |
|---|---|---|
| **GitHub** (this repo) | Where emails are written, reviewed, tested and released | The MDX masters, the components, the field contract, the release bundles |
| **Postmark** | Where emails are stored and sent | The compiled templates, pushed from a release; delivery, bounces, suppressions, unsubscribes |
| **Servantium** (the backend) | Decides who gets which email, and when | The events that trigger emails, and the code that sends a template by alias with its data |

## The path of a change

```
  edit src/emails/task.mdx
          │  pull request
          ▼
  ┌──────────────────────────────────────────────┐
  │ GitHub Actions: build, test, check images    │  the rendered gallery is attached to
  │ (masters → HTML, plain text, contract)       │  the run, so reviewers see every email
  └──────────────────────┬───────────────────────┘
                         │  merge to main, then tag grove-email@X.Y.Z
                         ▼
  ┌──────────────────────────────────────────────┐
  │ GitHub release                               │  the Postmark-ready templates and
  │ grove-email-X.Y.Z.tar.gz                     │  the contract, as downloadable files
  └──────────────────────┬───────────────────────┘
  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─  engineering's side from here  ─ ─ ─ ─ ─ ─
                         ▼
  ┌──────────────────────────────────────────────┐
  │ Postmark QA, then production                 │  templates pushed from the release,
  │                                              │  by alias
  └──────────────────────┬───────────────────────┘
                         ▼
  ┌──────────────────────────────────────────────┐
  │ Servantium backend                           │  POST /email/withTemplate
  │ TemplateAlias: "task"                        │  with the TemplateModel the
  │ TemplateModel: { actor_name, task_name, … }  │  contract describes
  └──────────────────────────────────────────────┘
```

This repo's workflow, [`.github/workflows/grove-email.yml`](../../../.github/workflows/grove-email.yml), stops at the release. It needs no secrets. Pushing templates into Postmark and sending them is engineering's; [engineering-handover.md](./engineering-handover.md) says what to build.

## What the build makes

`npm run build` reads every master in `src/emails/` and writes `dist/`, plus two generated docs:

| Output | For |
|---|---|
| `dist/postmark/<alias>/` | The template in the folder layout the Postmark CLI pushes: `content.html`, `content.txt`, `meta.json` |
| `dist/contract.json` | Every template's stream, sender, reply-to, subject and fields, with examples and notes |
| `dist/index.html` | The gallery: every email with its examples, at desktop and phone width |
| `dist/stylesheet.html` | The style guide, rendered |
| `dist/firebase/password-reset.html` | The reset email as a Firebase console template, while Firebase still sends resets |
| `docs/templates.md` | Every template and its fields, generated from the masters |
| `docs/style-guide.md` | The style guide as Markdown, generated from `src/stylesheet.ts` |

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

Each component is one file in [`src/components/`](../src/components/), with a header comment saying what it's for and how to use it, the same way Grove keeps one `.astro` file per component. [style-guide.md](./style-guide.md) is the full reference.

## Where facts come from

Nothing that appears in more than one email is typed into an email:

| Fact | Source | Changes reach |
|---|---|---|
| Colours, fonts | Verdant tokens (`packages/verdant`), synced by the build | emails released after the change |
| Address, footer links, help@, LinkedIn | [`packages/brand/company.json`](../../brand/company.json) | emails released after the change |
| Logo, banner art, icons | [`packages/brand/assets/`](../../brand/assets/), served from `assets.servantium.com` | emails released after the change |

Images load from permanent, fingerprinted addresses such as `https://assets.servantium.com/logo/servantium-logo-white.73c2cede0a.png`. A changed image gets a new address, so every email keeps showing what it was sent with, like the footer address. [The asset library](../../brand/docs/asset-library.md) explains the scheme.

## The rules are tests

`npm test` checks every email twice, as previewed and as sent, plus every style-guide sample:

- **Design:** one banner, no coloured side bars, one primary button, one-line titles.
- **Mail clients:** Gmail's 102 KB clip, SVG, flex, Outlook button shapes.
- **Accessibility:** every colour pair passes WCAG AA, every image has alt text, every email has a plain-text part.
- **Streams:** an unsubscribe link on broadcast mail only.
- **The contract:** every field is declared, used, and visible to Postmark.
- **Images:** every image in a sent email is a current fingerprinted address.
- **Docs:** the generated pages are current.

A broken rule fails the pull request, so a rule can only change by changing the test.

## Who does what

| | Design system | Engineering |
|---|---|---|
| Emails: copy, layout, components, rules | owns | reviews (CODEOWNERS) |
| Brand images, the asset library, company facts | owns | |
| The field contract | proposes in the pull request | reviews and approves |
| Tagging an email release | owns | |
| Postmark: account, servers, streams, sender domain, tokens | | owns |
| The workflow that pushes a release into Postmark | | owns |
| Sending: which event triggers which alias, with which data | | owns |
| Support inbound: help@ to a ticket, threading replies | | owns |
| Testing real sends in QA | | owns |

## Why it's built this way

- **One source.** An email exists once, in git. Postmark holds copies it's given, and edits made in Postmark's editor are overwritten on the next push.
- **The backend sends data, not HTML.** MDX is compiled at build time, never at send time. Compiling evaluates code, which Cloudflare Workers forbid, and product code shouldn't render email anyway. The backend picks an alias and supplies fields.
- **A release is the handover.** A tagged release is a fixed, downloadable bundle. Engineering can push it to Postmark from any pipeline they like, and roll back by pushing an older one.
- **Postmark-native.** Merge tags, optional sections and repeated rows are all Postmark's own Mustachio features, so there's no rendering service to run.
- **Plain HTML email.** Tables, inline styles, a VML button shape for Outlook, and images that degrade to a flat colour. Nothing depends on a client doing the modern thing.
