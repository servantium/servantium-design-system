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

## Two ways to write an email

| | TSX, in `src/templates/` | MDX, in `src/emails/` |
|---|---|---|
| For | Product emails. The words are fixed; the product supplies the data. | Emails a person writes, or that non-engineers should be able to edit. |
| Today | welcome, password-reset, task-notification, regulatory-notice | release notes, incident, maintenance, incident-resolved |
| Data | Typed props, with `placeholders` for the sender | `{{ merge_fields }}` anywhere, with `preview` values |

Both kinds come out the same way: as a Postmark template with an HTML part and a text part. Nothing downstream can tell them apart.

### Writing MDX

```mdx
---
subject: "Scheduled maintenance on {{ date }}"
preheader: "Servantium will be unavailable for up to {{ duration }}."
label: Scheduled maintenance
title: "Planned maintenance on {{ date }}"
tone: attention
stream: transactional
footer:
  reason: "You're receiving this because you're an administrator of {{ workspace_name }}."
preview:
  date: Saturday, Oct 24
  duration: 2 hours
  workspace_name: Halcyon Bioanalytical Services
---
Hi {{ first_name }},

<DataTable variant="outline" rows={[["Starts", "{{ starts }}"], ["Ends by", "{{ ends }}"]]} />

<Button href="{{ status_url }}" variant="secondary">View the status page</Button>
```

- **Frontmatter builds the frame**: the banner, the footer and the stream. It's validated like a schema. A missing `footer.reason`, an unknown tone, or Astro on an urgent email fails the build with a sentence saying what's wrong.
- **The body is Markdown plus the style-sheet components.** A paragraph becomes `Text`, `##` becomes `Heading`, `-` becomes `List`, `---` becomes `Divider`. Components need no import.
- **`{{ field }}` works anywhere**: in text, in a component prop, and in the frontmatter. It reaches Postmark untouched. The gallery fills it from `preview`. Inside a component, write the field as a string: `"{{ field }}"`.
- Add the file to `src/emails/`, run `npm run build`, and it shows up in the gallery, the tests and the Postmark export.

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

That is the folder layout the [Postmark CLI](https://github.com/ActiveCampaign/postmark-cli/wiki/templates-command) reads. It also writes `dist/postmark/send.json`, which gives each alias's stream and the model it expects, with sample values.

```bash
postmark templates push dist/postmark    # needs POSTMARK_SERVER_TOKEN — see "Before real sends"
```

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
- A bad frontmatter field.

One known exception is recorded as a test rather than hidden. **The primary button is white on #00C26D, about 2.3:1**, which is a design decision. Changing the fill to `#037A47` would pass.

## Before real sends

- **Host the images.** Sent templates load from `https://assets.servantium.com/brand/…`, which is proposed, not live (see `@servantium/brand` → Hosting). Don't push `dist/postmark/` until it is. `ASSET_BASE=… npm run build` points the export elsewhere.
- **Postmark access.** A server token in a secret store, never in the repo. Separate sending subdomains for transactional and broadcast mail, so a marketing complaint can't hurt password resets.
- **Test in real clients.** Everything follows Outlook- and Gmail-safe patterns and is checked in a browser at 640 and 375px. None of it has been through Outlook desktop, Gmail or Apple Mail yet. A Litmus or Email on Acid run is the next step.
- **Status page.** The incident and maintenance emails link to `{{ status_url }}`. `status.servantium.com` doesn't exist yet.
- **Sample content.** The regulatory notice, incident and maintenance values are illustrative. Release notes come from the help site. Confirm the picks with engineering before sending.
