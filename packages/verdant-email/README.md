# @servantium/verdant-email

Verdant for email: the components that build Servantium's emails, the emails themselves, and the style sheet. Colours come from `@servantium/verdant`. The logo, Astro, the banner art, the address and the footer links come from `@servantium/brand`. This package defines no brand values of its own.

```bash
npm run build          # sync Verdant tokens, render everything to dist/
npm test               # the rules, checked against every email
open dist/index.html   # every email, at desktop and phone width
open dist/stylesheet.html
```

**Start with `dist/stylesheet.html`.** It lists every frontmatter field, tone, component and rule, with the MDX for each one next to the email it makes.

## The banner

Every email opens on the same banner. It has the forest night sky, the logo, a dot and a label, and a headline. It comes in three **tones**. Each tone is chosen by answering one question: *is something wrong?*

| Tone | Answer | Use for |
|---|---|---|
| `default` | No | Almost everything: welcome, reset, tasks, release notes, required notices, "resolved" |
| `attention` | Not yet, but the reader needs to act or plan | Scheduled maintenance, a trial ending, a failed payment |
| `urgent` | Yes, it's broken now | An outage, a security incident. Rare, by design. |

A tone colours three things: the rule along the banner's bottom edge, the dot beside the label, and any callout in the body. The banner itself never changes.

**Astro** appears only when the email is good news *and* not urgent: welcome, milestones, release notes, marketing. He never appears on:

- security mail
- attention or urgent mail
- "resolved" notices
- legal, billing or money mail
- frequent notifications

The build enforces the attention/urgent rule. The others are listed in the style sheet for reviewers.

Outlook desktop ignores background images, so there the banner shows as flat forest. The text is designed to read on flat forest first.

## The masters

Every email is one MDX file in `src/emails/`. The file name is its Postmark template alias. There is no other copy to keep in step: the gallery, the tests, the Postmark templates and the field contract are all generated from these files.

| Master | Stream | Sent by |
|---|---|---|
| `welcome.mdx` | transactional | Backend, when an admin adds a user. This is also the invitation. |
| `password-reset.mdx` | transactional | Backend callable. Until then, Firebase sends a pasted copy. |
| `task-notification.mdx` | transactional | Backend, when a task's assignee changes. |
| `regulatory-notice.mdx` | transactional | A person, to every workspace admin. |
| `incident.mdx`, `maintenance.mdx`, `incident-resolved.mdx` | transactional | Later. The status page covers incidents first. |
| `release-notes-<month>.mdx` | broadcast | A monthly job, in batches of 500. |

### Writing one

```mdx
---
subject: "{{ assigner_name }} assigned you: {{ task_name }}"
preheader: "Due {{ due }} · {{ engagement }}"
label: Task
title: "{{ assigner_name }} assigned you a task"
stream: transactional
footer:
  reason: "You're receiving this because you were assigned a task in {{ workspace_name }}."
fields:
  assigner_name: { example: Jules Hart, note: Who made the assignment }
  task_name: { example: Clinical sample manifest reconciliation }
  due: { example: "Fri, Oct 16, 2026" }
  engagement: { example: AUR-417 — Phase II }
  note: { example: "Flag anything outside tolerance.", optional: true }
  task_url: { example: "https://app.servantium.com/…" }
  workspace_name: { example: Halcyon Bioanalytical Services }
---
<DataTable title="{{ task_name }}" rows={[["Due", <b>{"{{ due }}"}</b>]]} />

<If field="note">
  <Callout tone="neutral" title="Their note">“{{ . }}”</Callout>
</If>

<Button href="{{ task_url }}">Open task</Button>
```

- **The frontmatter builds the frame**: the banner, the footer and the stream. It's validated like a schema. A missing `footer.reason`, an unknown tone, or Astro on an urgent email fails the build with a sentence saying what's wrong.
- **`fields` is the contract with engineering.** Every `{{ field }}` the email uses must be declared, with an example and, where useful, a note on where the value comes from. The build fails if the email uses a field it doesn't declare, or declares one it never uses. The build writes all of them to `dist/contract.json`.
- **The body is Markdown plus the style-sheet components.** A paragraph becomes `Text`, `##` becomes `Heading`, `-` becomes `List`, `---` becomes `Divider`. Components need no import.
- **`{{ field }}` works anywhere**: in text, in a component prop, and in the frontmatter. It reaches Postmark untouched. The gallery fills it with the examples.
- **`<If field="x">`** shows its content only when the sender supplies `x`. Inside, `{{ . }}` is that value. Nothing else can be referenced inside, because Postmark scopes sections; the build enforces that.
- **`<Editable field="x">default</Editable>`** is copy an admin can override later without a template change. The sender passes `x` to replace the default.
- **`<CompanyLink to="app" />`** and **`<Button to="trust">`** take addresses from `company.json`, so they move when the address does.

### Release notes are drafted, not written twice

```bash
node scripts/draft-release-notes.mjs --from ../../../servantium-help/src/content/docs/help/release-notes \
  --month 2026-06 --pick "Secure Search,Contact Workspaces,Inline Custom Properties,Roles & Permissions"
```

The script reads that month's published notes from the help site and writes `src/emails/release-notes-<month>.mdx`. The draft has:

- the picked highlights, in the help site's own words
- a count of everything else
- a link to the full notes
- a comment listing every feature that wasn't picked, so an editor can swap one in

The help site stays the record. It skips `upcoming-release.mdx`, which is marked `published` but describes changes still in testing.

## Sending: Postmark

The build writes `dist/postmark/<alias>/` for every email:

- `content.html`
- `content.txt`
- `meta.json`

That is the folder layout the [Postmark CLI](https://github.com/ActiveCampaign/postmark-cli/wiki/templates-command) reads. The build also writes `dist/contract.json`: each alias's stream, who sends it, and every field with an example and a note.

**The pipeline** (`.github/workflows/email-templates.yml`, not yet run) follows the backend's own rhythm:

- **Pull request:** build and test. The gallery is attached to the run for review.
- **Merge to main:** push every template to the Postmark QA server.
- **Tag `email-v*`:** push every template to the Postmark production server.

Before each push, `scripts/postmark-validate.mjs` asks Postmark itself to render every template, with and without the optional fields. Postmark is a deployment target only: edits made in its UI are overwritten on the next push.

Product code then sends by alias and supplies only the data:

```python
# postmarker (Python); the Node client's sendEmailWithTemplate takes the same fields
postmark.emails.send_with_template(
    TemplateAlias="task-notification",
    TemplateModel={"assigner_name": "...", "task_name": "...", ...},
    To=assignee_email, From="Servantium <noreply@servantium.com>",
    MessageStream="outbound",
)
```

To change an email's design or wording, edit it here and push the templates again. Product code doesn't change.

**Streams.** Every email names its stream.

- `transactional` (Postmark's `outbound`) is mail about this person's account or something they did. It must always arrive and never carries an unsubscribe link.
- `broadcast` is optional mail sent to many people. Postmark requires an unsubscribe link there, so broadcast emails get `{{{ pm:unsubscribe }}}` in the footer automatically.

The tests fail if either rule is broken.

**Plain text** is derived from the HTML, so nobody maintains a second copy. Buttons become `Label (url)` and table rows become `Label: value`.

**Why templates, not rendering at send time.** Compiling MDX evaluates code, which Cloudflare Workers don't allow. More importantly, this way a design change doesn't need a product deploy.

### Password reset

Firebase sends the reset email today. To match, paste `dist/firebase/password-reset.html` into Firebase → Authentication → Templates → Password reset → Message. Firebase fills `%LINK%` and `%EMAIL%`. While you're there, change **Sender name** from "Max" to "Servantium".

This is a pasted copy, so it won't follow later design changes. The better path is for the backend to generate the link with the Admin SDK (`generate_password_reset_link`) and send the `password-reset` Postmark template like every other email.

## The rules

`npm test` checks every email, both the preview and the version that gets sent, plus every style-sheet sample. It fails on any of these:

- A coloured bar down the left of anything. Callouts carry their tone as a full tint instead.
- Astro on attention or urgent mail.
- An unsubscribe link on transactional mail, or none on broadcast mail.
- More than one primary button.
- An address or footer link typed into an email instead of coming from `company.json`.
- An email over 102 KB (Gmail clips longer messages).
- SVG, flex or grid.
- An image with no alt text.
- A button without its Outlook shape.
- A sent email whose images don't load from an absolute URL.
- An email with no readable plain-text part.
- A text colour pair below WCAG AA (4.5:1), or a tone rule below 3:1 on the banner.
- A bad frontmatter field, a field used but not declared, or declared but never used.
- A field referenced inside an `<If>` or `<Editable>` section other than the section's own.

One known exception is recorded as a test rather than hidden. **The primary button is white on #00C26D, about 2.3:1**, which is a design decision. Changing the fill to `#037A47` would pass.

## Before real sends

- **Host the images.** Sent templates load from `https://assets.servantium.com/brand/…`, which is proposed, not live (see `@servantium/brand` → Hosting). Don't push `dist/postmark/` until it is. `ASSET_BASE=… npm run build` points the export elsewhere.
- **Postmark account.** Two servers, QA and production, each with a transactional and a broadcast stream. Domain verification (DKIM and Return-Path DNS records). Tokens in GitHub secrets for the pipeline and in Firebase secrets for the backend — never in the repo.
- **Validate once by hand.** Run `scripts/postmark-validate.mjs` against the QA server before the pipeline's first push; it's the only check against Postmark's own engine.
- **Test in real clients.** Everything follows Outlook- and Gmail-safe patterns and is checked in a browser at 640 and 375px. None of it has been through Outlook desktop, Gmail or Apple Mail yet. A Litmus or Email on Acid run is the next step.
- **Status page.** The incident and maintenance emails link to `{{ status_url }}`. `status.servantium.com` doesn't exist yet.
- **Sample content.** The regulatory notice, incident and maintenance values are illustrative. Release notes come from the help site. Confirm the picks with engineering before sending.
