# Engineering handover: system email

This is everything engineering needs to connect Servantium's system emails to Postmark and the backend. The design system's side is done: the emails are written, tested and released from this repo. Everything below the line in [how-it-works.md](./how-it-works.md#the-path-of-a-change) is engineering's to build.

| Design system has done | Engineering builds |
|---|---|
| 13 emails as MDX masters, with a checked field contract | The Postmark account, servers, streams and sender domain |
| Components, rules and tests | A workflow that pushes a release into Postmark QA, then production |
| Brand images at `assets.servantium.com` | Backend code that sends each email by alias with its data |
| A GitHub release per version, with the Postmark-ready bundle | Support inbound (help@ to a ticket), when support moves in-product |
| This handover, the docs, and the [template catalogue](./templates.md) | Testing real sends |

## 1. What a release gives you

Each email release is a git tag, `email-vX.Y.Z`, and a GitHub release on [servantium/servantium-design-system](https://github.com/servantium/servantium-design-system/releases). The repo is public, so no credentials are needed to download one.

| File | What it is |
|---|---|
| `grove-email-email-vX.Y.Z.tar.gz` | `postmark/<alias>/{content.html, content.txt, meta.json}` for every template, plus `contract.json`, `servantium_email_contract.py` and `firebase/password-reset.html` |
| `contract.json` | Every template's stream, sender, reply-to, subject and fields, with notes and examples |
| `servantium_email_contract.py` | The same contract as Python `TypedDict`s: one per template, `NotRequired` for optional fields, and a `TEMPLATES` table of alias → stream and type |

```bash
gh release download email-v0.1.0 --repo servantium/servantium-design-system
tar -xzf grove-email-email-v0.1.0.tar.gz
```

The same files come from `npm run build` in `packages/grove-email` (they land in `dist/`), and every workflow run attaches them as the `grove-email` artifact.

## 2. Postmark setup

| Item | Recommendation |
|---|---|
| Servers | Two: **QA** and **Production**. Each has its own server token. |
| Streams | On each server, the default transactional stream (`outbound`) and a broadcast stream with the ID `broadcast`. The contract names these IDs. |
| Sender | Verify the `servantium.com` domain: DKIM, plus a custom Return-Path (Postmark gives the CNAME). Send from `Servantium <notifications@servantium.com>`. |
| Reply-To | `help@servantium.com`, which is monitored. Several emails invite a reply. |
| Tracking | Open tracking is your call. Turn **link tracking off** for `welcome`, `welcome-organization` and `password-reset`: those links carry one-time codes and shouldn't be rewritten. |
| Suppressions | Postmark suppresses hard bounces and spam complaints per stream automatically. Optionally, take the bounce and spam webhooks to flag bad addresses in the app. |
| Templates | Pushed only from a release. Treat Postmark's template editor as read-only: the next push overwrites any edit made there. |

## 3. The workflow to build

The job is to push a release's templates into Postmark QA, then, after an approval, the same bundle into production. Where it lives is your choice: engineering's own repo, or a workflow in this one using your secrets.

Pushing uses the official [Postmark CLI](https://github.com/ActiveCampaign/postmark-cli), which reads exactly the folder layout in the bundle. `scripts/postmark-validate.mjs` in this package asks Postmark's own template engine to render every template, with and without its optional fields, before you push.

A reference version (not active anywhere):

```yaml
name: Email templates → Postmark
on:
  workflow_dispatch:
    inputs:
      tag: { description: 'Email release, e.g. email-v0.1.0', required: true }
jobs:
  qa:
    runs-on: ubuntu-latest
    env: { POSTMARK_SERVER_TOKEN: '${{ secrets.POSTMARK_SERVER_TOKEN_QA }}' }
    steps:
      - run: gh release download "${{ inputs.tag }}" --repo servantium/servantium-design-system --pattern '*.tar.gz'
        env: { GH_TOKEN: '${{ github.token }}' }
      - run: mkdir dist && tar -xzf grove-email-*.tar.gz -C dist
      - uses: actions/checkout@v4
        with: { repository: servantium/servantium-design-system, ref: '${{ inputs.tag }}', path: ds, sparse-checkout: packages/grove-email/scripts }
      - run: cp -r dist ds/packages/grove-email/dist && node ds/packages/grove-email/scripts/postmark-validate.mjs
      - run: npx --yes postmark-cli templates push dist/postmark --force --all
  production:
    needs: qa
    runs-on: ubuntu-latest
    environment: production        # required reviewers here
    env: { POSTMARK_SERVER_TOKEN: '${{ secrets.POSTMARK_SERVER_TOKEN_PRODUCTION }}' }
    steps:
      - run: gh release download "${{ inputs.tag }}" --repo servantium/servantium-design-system --pattern '*.tar.gz'
        env: { GH_TOKEN: '${{ github.token }}' }
      - run: mkdir dist && tar -xzf grove-email-*.tar.gz -C dist
      - run: npx --yes postmark-cli templates push dist/postmark --force --all
```

Notes:

- A push adds and updates templates. It never deletes one. When a template is retired, remove it from both servers by hand.
- Rolling back means pushing the previous release.
- The validator hasn't been run against a real Postmark server yet. Run it once by hand against QA first.

## 4. Sending from the backend

Every send is one call: `POST https://api.postmarkapp.com/email/withTemplate` with the server token in `X-Postmark-Server-Token`.

```python
import requests
from servantium_email_contract import FROM, REPLY_TO, TEMPLATES, TaskData

def send(alias: str, to: str, model: dict, token: str) -> None:
    requests.post(
        "https://api.postmarkapp.com/email/withTemplate",
        headers={"X-Postmark-Server-Token": token, "Accept": "application/json"},
        json={
            "From": FROM,
            "To": to,
            "ReplyTo": REPLY_TO,
            "MessageStream": TEMPLATES[alias]["message_stream"],
            "TemplateAlias": alias,
            "TemplateModel": model,
            "Tag": alias,
        },
        timeout=10,
    ).raise_for_status()

model: TaskData = {
    "actor_name": "Jules Hart",
    "action": "assigned you",
    "task_name": "Clinical sample manifest reconciliation",
    "due": "Fri, Oct 16, 2026",          # formatted for the recipient: the template never formats
    "status": "Not started",
    "engagement": "AUR-417 — Phase II Immunogenicity & PK",
    "client": "Aurora Pharmaceuticals",
    "task_url": "https://app.servantium.com/engagements/eng-aur-417/project_plans?task=ppi-manifest",
    "organization_name": "Halcyon Bioanalytical Services",
    # "message" and "plan_url" are optional: leave them out and their sections disappear
}
send("task", "priya.nair@halcyon.example", model, token)
```

Rules that apply to every email:

- **Format before sending.** Dates in the reader's time zone, money with its currency, names as written. Postmark prints exactly what it receives. [fields.md](./fields.md) has the conventions.
- **Leave optional fields out** when there's nothing to show. An empty string also hides the section.
- **Send plain text in fields, never HTML.** Postmark escapes it.
- **Tag each send with its alias** (`Tag`), and put IDs you'll want when debugging in `Metadata`, such as the organization ID.

### When each email is sent

| Alias | Trigger | Phase | Notes |
|---|---|---|---|
| `welcome` | An admin adds a person to an organization | v1 | Also the invitation: `set_password_url` from Firebase Admin `generatePasswordResetLink(email)`. |
| `welcome-organization` | A new organization is created | v1 | To its first administrator, with the same kind of link. |
| `password-reset` | "Forgot password" in the app | v1 | Until the backend sends it, Firebase does; see section 6. |
| `task` | A task is assigned, commented on, rescheduled or completed | v1 | One template for every task event; `action` says which. The assignee change is visible in the project-plan item trigger. |
| `notification` | Any other single event worth an email | v1 | Approvals, mentions, a quote changing status, a plan being published. |
| `release-notes` | Monthly, to active users | v1 | Broadcast stream. Send with `/email/batchWithTemplates`, up to 500 messages per call. Postmark adds the unsubscribe link and skips anyone who has unsubscribed. |
| `digest` | Daily or weekly, for people who choose it | v2 | Needs notification preferences in the app first. At most ten `items`; put the count of the rest in `more`. |
| `support-received` | A request reaches help@ | v2 | The automatic first reply. |
| `support-reply` | Our team replies, asks, or resolves | v2 | See "Support threading" below. |
| `incident` | An incident opens, and at each status change | later | After a status page exists. To each administrator of an affected organization. |
| `incident-resolved` | The incident is over | later | |
| `maintenance` | 72 hours before planned downtime | later | |
| `regulatory-notice` | As a customer's DPA or contract requires | later | The change itself comes in as data (`change_summary`, `change_details`). Legal review pending. |

Every template's full field list, with notes and examples, is in [templates.md](./templates.md).

### Support threading (v2)

Each request is one conversation, in the customer's inbox and in ours:

- **Subject:** every message uses `[#1042] <their original subject>`. The ticket title is the customer's subject with any `Re:` or `Fwd:` removed.
- **Headers:** each reply sets `In-Reply-To` and `References` to the previous message's `Message-ID`.
- **Reply-To:** set per request, so a reply finds its ticket. To match an incoming reply, check in this order:
  1. the plus-address hash (Postmark's `MailboxHash`), if replies reach Postmark on a plus address;
  2. the `In-Reply-To` and `References` headers;
  3. the `[#id]` in the subject.
- **Where replies go:** `help@servantium.com` is a Google Workspace mailbox. For replies to reach Postmark's inbound webhook, either give a subdomain an MX record pointing at Postmark (for example, replies to `help+1042@reply.servantium.com`), or forward from Google. With forwarding, rely on the headers and the subject rather than the hash.
- **Reply text:** use Postmark's `StrippedTextReply` for the new message, and keep the earlier messages as `thread` items, newest first, each trimmed to 300 characters.

## 5. Brand images

Every image in a sent email loads from `https://assets.servantium.com/<path>.<fingerprint>.<ext>`: a Cloudflare R2 bucket the design system owns. Addresses are permanent and never overwritten. There's nothing for engineering to set up here. The design system publishes images, and the checks in this repo fail if a template refers to an image that isn't live. [The asset library](../../brand/docs/asset-library.md) has the details.

## 6. The Firebase password reset, for now

Until the backend sends `password-reset` through Postmark, Firebase sends its own reset email. `firebase/password-reset.html` in the bundle is the Servantium design as a Firebase console template: a body fragment, with Firebase's `%LINK%` and `%EMAIL%` placeholders.

In the Firebase console, open Authentication → Templates → Password reset. Paste it into the message, and set the sender name to "Servantium".

## 7. Testing

- Run `postmark-validate.mjs` against QA once, then push.
- Send every v1 template from QA to test inboxes in:
  - Outlook desktop (Windows)
  - Outlook.com
  - Gmail on the web and on a phone
  - Apple Mail on macOS and iOS
- Check each one with images off, in dark mode, and in its plain-text version.
- Send each template with its optional fields missing. Sections should disappear cleanly, with no empty panels.
- Check that images load from `assets.servantium.com`, and that `password-reset` and `welcome` links aren't rewritten by tracking.

## 8. Before the first real send

| | Owner |
|---|---|
| Asset library live at `assets.servantium.com` | Design system |
| First email release tagged | Design system |
| Postmark servers, streams, sender domain, tokens | Engineering |
| Workflow pushing a release into QA and production | Engineering |
| v1 aliases wired in the backend | Engineering |
| Test sends across clients (section 7) | Engineering |
| Legal review of `regulatory-notice` | Design system |
| Status footer link switched on, once the status page exists (`packages/brand/company.json`) | Design system |

## Where everything is

| What | Where |
|---|---|
| The emails | [`src/emails/`](../src/emails/), one `.mdx` per template, named for its alias |
| Every template and its fields | [templates.md](./templates.md) (generated) |
| How it fits together | [how-it-works.md](./how-it-works.md) |
| Field naming, formatting, safe changes | [fields.md](./fields.md) |
| Writing or changing an email | [writing-an-email.md](./writing-an-email.md) |
| Components and rules | [style-guide.md](./style-guide.md) (generated) |
| Releases, templates, images | [maintaining.md](./maintaining.md) |
| The asset library | [`packages/brand/docs/asset-library.md`](../../brand/docs/asset-library.md) |
| Releases | [github.com/servantium/servantium-design-system/releases](https://github.com/servantium/servantium-design-system/releases) |
