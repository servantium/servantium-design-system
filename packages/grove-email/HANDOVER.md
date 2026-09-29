# Handover: Servantium's system emails

**For engineering. Start here.** This page is the summary; [docs/engineering-handover.md](./docs/engineering-handover.md) has the detail.

| | |
|---|---|
| **What** | 13 system emails, written and tested in this repo, released as Postmark-ready templates with a typed data contract |
| **Latest release** | [Releases tagged `grove-email@…`](https://github.com/servantium/servantium-design-system/releases) · [changelog](./CHANGELOG.md) |
| **Design system owns** | The emails, the components and rules, the images at `assets.servantium.com`, and the releases |
| **Engineering owns** | Postmark, pushing a release into it, and sending from the backend |

## In one minute

- **Where the emails live.** Every email is one MDX file in [`src/emails/`](./src/emails/). The file name is the Postmark template alias.
- **How they ship.** A GitHub workflow builds and tests them. Each `grove-email@X.Y.Z` tag publishes a GitHub release with the templates in Postmark's folder layout, plus the contract. You push that release into Postmark.
- **How to send one.** The backend calls Postmark's `/email/withTemplate` with an alias and a `TemplateModel`. It never builds email HTML.
- **The contract.** Each email declares its fields. Every release carries them as `contract.json` and as Python `TypedDict`s (`servantium_email_contract.py`). [docs/templates.md](./docs/templates.md) lists every field with its note and example.
- **Images.** Every image loads from a permanent, fingerprinted address at `assets.servantium.com`. A changed image gets a new address, so an email already sent never changes. The domain is kept out of search results.

## The path of a change

1. **Edit** an email's `.mdx` file in this repo.
2. **Pull request:** build and 39 tests, plus a check that every image is live. Engineering reviews contract changes ([CODEOWNERS](../../.github/CODEOWNERS)).
3. **Release:** a `grove-email@X.Y.Z` tag publishes the bundle as a GitHub release. It's public, so no credentials are needed to download it.
4. **Postmark** *(engineering)*: your workflow validates the release against QA, pushes it, then promotes the same bundle to production.
5. **Send** *(engineering)*: the backend sends by alias with data that matches the contract.

## What engineering sets up

| Area | Work |
|---|---|
| **Postmark** | Two servers, QA and production, each with `outbound` and `broadcast` streams. The `servantium.com` sender domain (DKIM, Return-Path). From `notifications@servantium.com`, Reply-To `help@servantium.com`. Link tracking off for `welcome`, `welcome-organization` and `password-reset`. |
| **A push workflow** | Download a release, run `scripts/postmark-validate.mjs` against QA, push with the Postmark CLI, then promote to production behind an approval. There's a [reference workflow](./docs/engineering-handover.md#3-the-workflow-to-build). |
| **The backend** | Map each event to an alias ([when each email is sent](./docs/engineering-handover.md#when-each-email-is-sent)). Build the `TemplateModel` from the contract, and format dates, money and names first. Leave optional fields out. |
| **For now** | Until the backend sends resets, paste `firebase/password-reset.html` from the release into the Firebase console. |

## The emails

| Alias | Sent when | Phase |
|---|---|---|
| `welcome` | An admin adds a person to an organization | v1 |
| `welcome-organization` | A new organization is created | v1 |
| `password-reset` | "Forgot password" | v1 |
| `task` | A task is assigned, commented on, rescheduled or completed | v1 |
| `notification` | Any other single event worth an email | v1 |
| `release-notes` | Monthly, to active users (broadcast stream) | v1 |
| `digest` | Daily or weekly, for people who choose it | v2 |
| `support-received` | A request reaches help@ | v2 |
| `support-reply` | Our team replies, asks, or resolves | v2 |
| `incident` | A service disruption, and each status change | later |
| `incident-resolved` | The disruption is over | later |
| `maintenance` | 72 hours before planned downtime | later |
| `regulatory-notice` | As a customer's DPA or contract requires | later |

## Links

| What | Where |
|---|---|
| The full handover | [docs/engineering-handover.md](./docs/engineering-handover.md) |
| Every template and field | [docs/templates.md](./docs/templates.md) |
| How it fits together | [docs/how-it-works.md](./docs/how-it-works.md) |
| Field naming and formatting | [docs/fields.md](./docs/fields.md) |
| Releases and maintenance | [docs/maintaining.md](./docs/maintaining.md) |
| The emails | [src/emails/](./src/emails/) |
| The workflow | [.github/workflows/grove-email.yml](../../.github/workflows/grove-email.yml) |
| The Postmark validator | [scripts/postmark-validate.mjs](./scripts/postmark-validate.mjs) |
| The asset library | [../brand/docs/asset-library.md](../brand/docs/asset-library.md) · [catalogue](https://assets.servantium.com/index.html) |
