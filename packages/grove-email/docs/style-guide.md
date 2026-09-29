# Email style guide

<!-- GENERATED from src/stylesheet.ts by `npm run build`. Edit that file, not this one; `npm test` fails if this page is stale. -->

Everything an email may contain, and the rules each one follows. The same content, rendered, is `dist/stylesheet.html` after a build. For the walk-through of writing a new email, start with [writing-an-email.md](./writing-an-email.md).

- [Frontmatter](#frontmatter)
- [Tones](#tones)
- [Writing](#writing)
- [Actions](#actions)
- [Data](#data)
- [Emphasis](#emphasis)
- [Lists the sender fills](#lists-the-sender-fills)
- [Merge fields](#merge-fields)
- [Optional and editable content](#optional-and-editable-content)
- [Writing rules](#writing-rules)
- [Accessibility](#accessibility)
- [Banned](#banned)

## Frontmatter

The block at the top of a master builds the frame (banner, footer, stream) and declares the data the email needs. It's validated like a schema: a broken rule fails the build with a sentence.

| Key | | Values | Notes |
|---|---|---|---|
| `subject` | required | text, may use {{ fields }} | The inbox line. Say what happened, not "Update from Servantium". |
| `preheader` | required | text | The grey line after the subject. Add something the subject doesn't say. |
| `label` | required | text, 16 characters at most | Top-right of the banner: what kind of email this is. "Release notes", "Task", "Service status". |
| `title` | required | text, 24 characters at most, no fields | The banner’s one line — the same on every send, so it never wraps. The event’s details go in the body. |
| `tone` | optional | default · attention · urgent | Defaults to default. See Tones. |
| `astro` | optional | a pose from packages/brand/assets/astro: waving, captain, explorer… | The mascot. Off for now: no email uses it. The banner keeps room for one, and the build still refuses it on attention or urgent mail. |
| `stream` | required | transactional · broadcast | Which Postmark stream sends it. Broadcast gets an unsubscribe link; transactional never does. |
| `footer.reason` | required | text | Why this person got this email. The build fails without it. |
| `footer.settings` | optional | URL | Adds "Notification settings" to the footer, for notifications people can tune. |
| `fields` | required | name: { example, note, optional } | Every {{ field }} the email uses — the contract with engineering. The build fails if the email uses a field it doesn’t declare, or declares one it never uses. Examples fill the gallery; they are never sent. |
| `name · sends` | optional | text | A display name, and who sends it and when. Both go into the contract. |

```mdx
---
subject: "What's new in Servantium — June 2026"
preheader: "Secure Search, Contact Workspaces, and 83 more improvements."
label: Release notes
title: What's new in Servantium
stream: broadcast
footer:
  reason: Sent to Servantium users about product updates.
fields:
  first_name: { example: Jules, note: "From the user's profile" }
---
Hi {{ first_name }},

Here are the highlights from June.
```

## Tones

One question: **Is something wrong?** The banner never changes; a tone colours the dot beside the label, the rule under the banner, and any callout.

| Tone | Answer | Use it for | Examples |
|---|---|---|---|
| `default` | No | Almost everything. Nothing is wrong and nothing is late. | Welcome, password reset, tasks, release notes, required notices, "resolved" |
| `attention` | Not yet — but the reader needs to act or plan | Something will happen or has partly gone wrong, and the reader should do something about it soon. | Scheduled maintenance, a trial ending, a failed payment, a sync that needs reconnecting |
| `urgent` | Yes, it's broken now | Something is broken or unsafe right now. Rare, by design — if urgent is common, readers stop believing it. | An outage, a security incident, a suspicious sign-in |

## Writing

Plain Markdown. Each piece becomes an email-safe component, so there's nothing to import.

### Paragraph

Most of any email. Short paragraphs — two or three sentences.

**Source:** [`src/components/Text.tsx`](../src/components/Text.tsx)

```mdx
Paragraphs are plain Markdown. **Bold** for the one fact that matters, and [a link](https://help.servantium.com) where the reader might want more.
```

### Link

A Markdown link in running text. Write <Link> when the address is a field inside a component, or inside <If>. The words say where it goes.

**Not for:** “Click here” or a bare URL (except in LinkFallback).

**Props:** href

**Source:** [`src/components/Link.tsx`](../src/components/Link.tsx)

```mdx
Everything that changed is in the [release notes](https://help.servantium.com/release-notes/).

<Text size="sm" margin="0"><Link href="{{ plan_url }}">View the full project plan</Link></Text>
```

### Section heading

Splitting a longer email into parts a reader can scan. `##` only.

**Not for:** `#` — the banner already carries the headline.

**Source:** [`src/components/Heading.tsx`](../src/components/Heading.tsx)

```mdx
## What's changing

A heading is followed by at least one paragraph.
```

### Bulleted list

Three to five short, parallel items.

**Not for:** Lists of long paragraphs — use Items.

**Source:** [`src/components/List.tsx`](../src/components/List.tsx)

```mdx
- Drawn as a table, so bullets line up in Outlook
- One line each, where you can
- Numbered lists come out as bullets too
```

### Divider

A hard break between two unrelated parts. Rarely needed — a heading usually does the job.

**Source:** [`src/components/Divider.tsx`](../src/components/Divider.tsx)

```mdx
Above the line.

---

Below the line.
```

### Code

Internal and technical mail. Customers rarely need it.

**Source:** [`src/components/CodeBlock.tsx`](../src/components/CodeBlock.tsx)

```mdx
```
POSTMARK_TEMPLATE=incident
```
```

## Actions

One primary button per email. If there are two things to do, the second is a secondary button or a link.

### Button — primary

The one action the email exists for.

**Not for:** Legal notices, where a filled green button reads as a sales pitch.

**Props:** href · width (Outlook only — widen it for long labels)

**Source:** [`src/components/Button.tsx`](../src/components/Button.tsx)

```mdx
<Button href="https://app.servantium.com">Open Servantium</Button>
```

### Button — secondary

A second action, or the only action on a notice or incident.

**Props:** href · variant="secondary" · width

**Source:** [`src/components/Button.tsx`](../src/components/Button.tsx)

```mdx
<Button href="https://trust.servantium.com" variant="secondary" width={260}>View the sub-processor list</Button>
```

### Link fallback

Under any button whose link carries a one-time code — resets, invitations. Some clients break buttons; a pasted link always works.

**Props:** href

**Source:** [`src/components/LinkFallback.tsx`](../src/components/LinkFallback.tsx)

```mdx
<LinkFallback href="https://app.servantium.com/__/auth/action?mode=resetPassword&oobCode=Rt5nW2" />
```

## Data

For facts a reader will look up rather than read.

### Data table — panel

Details in the flow of a message: a task's dates, a quote's totals.

**Props:** rows · title · labelWidth

**Source:** [`src/components/DataTable.tsx`](../src/components/DataTable.tsx)

```mdx
<DataTable title="Clinical sample manifest reconciliation" labelWidth={112} rows={[
  ["Due", <b>Fri, Oct 16, 2026</b>],
  ["Engagement", "AUR-417 — Phase II Immunogenicity & PK"],
  ["Waiting on", "Project kickoff & study handoff"],
]} />
```

### Data table — outline

A record the reader will refer back to — a legal summary, an incident's timings.

**Props:** variant="outline" · rows · labelWidth

**Source:** [`src/components/DataTable.tsx`](../src/components/DataTable.tsx)

```mdx
<DataTable variant="outline" labelWidth={136} rows={[
  ["Effective date", <b>October 24, 2026</b>],
  ["Action required", "None"],
]} />
```

### Items

A run of titled things — release highlights, onboarding steps, incident updates.

**Props:** items: { title, body, chip?, meta? }[]

**Source:** [`src/components/Items.tsx`](../src/components/Items.tsx)

```mdx
<Items items={[
  { chip: { tone: "default", label: "New" }, title: "Secure Search", body: "Search only shows records you're allowed to see." },
  { chip: { tone: "attention", label: "Changed" }, meta: "Settings → Users", title: "User Management", body: "Click a person to assign roles and tags." },
]} />
```

### Steps

A short numbered sequence — “your first steps”. Each number sits on the line of its title.

**Not for:** Lists of things that aren’t a sequence — use Items.

**Props:** steps: { title, body }[]

**Source:** [`src/components/Steps.tsx`](../src/components/Steps.tsx)

```mdx
<Steps steps={[
  { title: "Invite your team", body: "Add people under Settings → Users." },
  { title: "Add your clients", body: "The accounts you do work for, under Clients." },
]} />
```

### Chip

A one-word status beside a title: New, Changed, Resolved, Beta.

**Props:** tone: default · attention · urgent · neutral

**Source:** [`src/components/Chip.tsx`](../src/components/Chip.tsx)

```mdx
<Chip>New</Chip> <Chip tone="attention">Changed</Chip> <Chip tone="urgent">Removed</Chip> <Chip tone="neutral">Beta</Chip>
```

## Emphasis

A callout is for the one thing a reader must not miss. One per email; if everything is highlighted, nothing is. The tone fills the whole panel — there is no coloured bar down the side, and there never will be.

### Callout

default: reassurance ("Didn't request this?"). attention: something to do. urgent: something to stop doing. neutral: a quoted note.

**Props:** tone · title

**Source:** [`src/components/Callout.tsx`](../src/components/Callout.tsx)

```mdx
<Callout title="Didn't request this?">You can ignore this email. Your password won't change.</Callout>

<Spacer size={12} />

<Callout tone="attention" title="Before the window starts">Save any open quotes or plans.</Callout>

<Spacer size={12} />

<Callout tone="urgent" title="Don't share this code">Servantium will never ask you for it.</Callout>

<Spacer size={12} />

<Callout tone="neutral" title="Jules Hart wrote">“Flag anything outside the 10% tolerance.”</Callout>
```

### Eyebrow

A breadcrumb above a heading or table title — a project code, a section.

**Source:** [`src/components/Eyebrow.tsx`](../src/components/Eyebrow.tsx)

```mdx
<Eyebrow>AUR-417 · Phase II</Eyebrow>

## Clinical sample manifest reconciliation
```

### Spacer

Space around components. Paragraphs space themselves; components don't.

**Props:** size (px, default 24)

**Source:** [`src/components/Spacer.tsx`](../src/components/Spacer.tsx)

```mdx
Text above.

<Spacer size={32} />

Text 32px below.
```

## Lists the sender fills

When the number of rows depends on the data — a day's updates, a reply's paragraphs, a conversation — the sender supplies a list and Postmark repeats the row. Declare the field with a list of example items; the build checks every item field the component reads.

### Updates

A digest of events: one row each, with a category chip, a time, a linked title and a line of context.

**Props:** field — a list of { category, time, title, context, url }

**Source:** [`src/components/Updates.tsx`](../src/components/Updates.tsx)

```mdx
<Updates field="items" />
```

### Paragraphs

Free text a person wrote — a support reply. The sender splits it on blank lines, one { text } per paragraph. Escaped, so a message can't inject HTML.

**Not for:** Copy we write ourselves — that goes in the master as Markdown.

**Props:** field — a list of { text }

**Source:** [`src/components/Paragraphs.tsx`](../src/components/Paragraphs.tsx)

```mdx
<Paragraphs field="reply" />
```

### Thread

The earlier messages in a conversation, newest first, quieter than the new message above them.

**Props:** field — a list of { author, time, excerpt } · title

**Source:** [`src/components/Thread.tsx`](../src/components/Thread.tsx)

```mdx
<Thread field="thread" title="Earlier in this conversation" />
```

## Merge fields

Anything the sender fills in. Write {{ field_name }} anywhere — text, a component, the frontmatter. It reaches Postmark untouched; the gallery fills it from `preview`.

### In text

Names, dates, anything specific to the reader.

```mdx
Hi {{ first_name }}, your quote for **{{ client }}** is ready.
```

### In a component

Inside a component, a field is a string: "{{ field }}". To make it bold, {"{{ field }}"} inside the tag.

**Props:** any string prop

```mdx
<DataTable rows={[
  ["Client", "{{ client }}"],
  ["Due", <b>{"{{ due }}"}</b>],
]} />

<Spacer size={20} />

<Button href="{{ quote_url }}">Open quote</Button>
```

## Optional and editable content

Two building blocks that Postmark understands natively. No new system is needed to hide content that has no data, or to let an admin replace a paragraph later.

### If — optional content

Content that should only appear when the sender supplies a field: a note, a reason, a comment. Inside, {{ . }} is that field’s value — Postmark scopes sections, so nothing else can be referenced inside.

**Props:** field

**Source:** [`src/components/If.tsx`](../src/components/If.tsx)

```mdx
<If field="note">
  <Callout tone="neutral" title="Their note">“{{ . }}”</Callout>
</If>

The rest of the email.
```

### Editable — a paragraph an admin can override

Copy a workspace admin might want to change later — an intro, a sign-off. The default shows until the sender passes a value for the field. Only text can change; the design can’t.

**Props:** field

**Source:** [`src/components/Editable.tsx`](../src/components/Editable.tsx)

```mdx
<Editable field="welcome_intro">Your team uses Servantium to scope, price and deliver every project.</Editable>
```

### Company link

Any link to a Servantium address in the body. The address comes from company.json, so moving the app or the trust centre updates every email. Buttons take `to` the same way.

**Props:** to: website · app · help · privacy · terms · trust · releaseNotes · status

**Source:** [`src/components/CompanyLink.tsx`](../src/components/CompanyLink.tsx)

```mdx
Sign in at <CompanyLink to="app" />.

<Button to="trust" variant="secondary" width={250}>View the trust centre</Button>
```

## Writing rules

| Rule | In practice |
|---|---|
| **The subject says what happened.** | “Jules Hart assigned you: Manifest reconciliation”, not “Update from Servantium”. Aim for 60 characters. |
| **The preheader adds something the subject doesn’t.** | A due date, an amount, the next step. Aim for 90 characters. |
| **The first line says what happened.** | The banner names the kind of email, the same on every send; the body’s first line says what happened and what it means for them. |
| **One primary action.** | Button labels are a verb and an object, 24 characters at most: “Open task”, “Set your password”. Never “Click here”. |
| **Links say where they go.** | “View the full project plan”, not “here”. Every link is also in the plain-text version. |
| **Plain, warm, specific.** | Short sentences, active voice, no jargon. One exclamation mark at most, and only for good news. |
| **Numbers are formatted before sending.** | Dates in the reader’s time zone, money with its currency. The template never formats; the sender does. |
| **Every email says why it arrived.** | `footer.reason` is required. If we can’t explain why someone got it, we shouldn’t send it. |

## Accessibility

| | |
|---|---|
| **Contrast** | Every text colour pair passes WCAG AA (4.5:1), including both button styles. The tests compute it. |
| **Type size** | Body text 16px, nothing smaller than 13px. Mobile keeps the same sizes. |
| **Structure** | The document declares its language; the banner headline is the one h1 and section headings are h2; layout tables are marked presentation so screen readers skip them. |
| **Images** | Every image has alt text or is decorative. No meaning lives only in an image — the email reads in full with images off. |
| **Colour is never the only signal** | An urgent email says so in words, in its label and headline; chips carry words too. |
| **Real links** | Buttons are ordinary links with visible text, so they work with keyboards, screen readers and plain-text mail. |
| **A plain-text version** | Generated from the HTML for every email, so nobody maintains a second copy. |

## Banned

"Enforced" means `npm test` fails; "review" means a person checks it in the pull request.

| Rule | | Why |
|---|---|---|
| A coloured bar down the left of a section | enforced | Design decision, 2026-09-24. Callouts carry their tone as a full tint. |
| Astro on attention or urgent mail | enforced | See Astro. |
| An unsubscribe link on transactional mail — or none on broadcast | enforced | Transactional mail must always arrive. Postmark requires one on broadcast. |
| SVG images | enforced | Gmail and Outlook drop them. |
| Flex or grid layout | enforced | Outlook desktop can't draw them. Everything is tables. |
| Images without alt text | enforced | Most Outlook users see alt text first; images are off by default. |
| Emails over 102 KB | enforced | Gmail cuts them off with "View entire message". |
| Addresses or footer links typed into an email | enforced | They come from company.json, so a change reaches every email. |
| More than one primary button | enforced | Two filled buttons compete; the reader picks neither. |
| Text in images | review | Invisible with images off, unreadable to screen readers, unsearchable. |
