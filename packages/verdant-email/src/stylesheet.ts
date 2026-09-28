/**
 * stylesheet — everything an email may contain, with an MDX sample for each.
 *
 * The export renders this to dist/stylesheet.html: the sample on the left, the real output on the
 * right. Every sample is compiled through the same MDX loader and components a real email uses,
 * and test/rules.test.tsx runs the rules over each one, so the style sheet can't show something
 * that doesn't work.
 */
import type { Tone } from './theme';

// ── Frontmatter ─────────────────────────────────────────────────────────────────────────────────
export const FRONTMATTER: { field: string; required: boolean; values: string; note: string }[] = [
  { field: 'subject', required: true, values: 'text, may use {{ fields }}', note: 'The inbox line. Say what happened, not "Update from Servantium".' },
  { field: 'preheader', required: true, values: 'text', note: 'The grey line after the subject. Add something the subject doesn\'t say.' },
  { field: 'label', required: true, values: 'text', note: 'Top-right of the banner: what kind of email this is. "Release notes", "Task", "Resolved".' },
  { field: 'title', required: true, values: 'text', note: 'The banner headline. Every email has one, so the body starts with content.' },
  { field: 'subtitle', required: false, values: 'text', note: 'One line under the headline.' },
  { field: 'tone', required: false, values: 'default · attention · urgent', note: 'Defaults to default. See Tones.' },
  { field: 'astro', required: false, values: 'waving · captain · detective · professor · cowboy', note: 'Only with the default tone — the build fails otherwise. See Astro.' },
  { field: 'stream', required: true, values: 'transactional · broadcast', note: 'Which Postmark stream sends it. Broadcast gets an unsubscribe link; transactional never does.' },
  { field: 'footer.reason', required: true, values: 'text', note: 'Why this person got this email. The build fails without it.' },
  { field: 'footer.settings', required: false, values: 'URL', note: 'Adds "Notification settings" to the footer, for notifications people can tune.' },
  { field: 'fields', required: true, values: 'name: { example, note, optional }', note: 'Every {{ field }} the email uses — the contract with engineering. The build fails if the email uses a field it doesn’t declare, or declares one it never uses. Examples fill the gallery; they are never sent.' },
  { field: 'name · sends', required: false, values: 'text', note: 'A display name, and who sends it and when. Both go into the contract.' },
];

export const FRONTMATTER_EXAMPLE = `---
subject: "What's new in Servantium — June 2026"
preheader: "Secure Search, Contact Workspaces, and 83 more improvements."
label: Release notes
title: What's new in Servantium
subtitle: June 2026
astro: professor
stream: broadcast
footer:
  reason: You're receiving product updates because you're a Servantium user.
fields:
  first_name: { example: Jules, note: "From the user's profile" }
---
Hi {{ first_name }},

Here are the highlights from June.`;

// ── Tones ───────────────────────────────────────────────────────────────────────────────────────
export const TONE_QUESTION = 'Is something wrong?';

export const TONE_GUIDE: Record<Tone, { answer: string; use: string; examples: string }> = {
  default: {
    answer: 'No',
    use: 'Almost everything. Nothing is wrong and nothing is late.',
    examples: 'Welcome, password reset, tasks, release notes, required notices, "resolved"',
  },
  attention: {
    answer: 'Not yet — but the reader needs to act or plan',
    use: 'Something will happen or has partly gone wrong, and the reader should do something about it soon.',
    examples: 'Scheduled maintenance, a trial ending, a failed payment, a sync that needs reconnecting',
  },
  urgent: {
    answer: 'Yes, it\'s broken now',
    use: 'Something is broken or unsafe right now. Rare, by design — if urgent is common, readers stop believing it.',
    examples: 'An outage, a security incident, a suspicious sign-in',
  },
};

// ── Astro ───────────────────────────────────────────────────────────────────────────────────────
export const ASTRO_RULE = 'Astro appears when the email is good news AND not urgent.';
export const ASTRO_USE = [
  'Welcome and onboarding',
  'Milestones — a first quote sent, a year with Servantium',
  'Release notes and product announcements',
  'Marketing and newsletters',
];
export const ASTRO_NEVER = [
  ['Security mail', 'A reset or sign-in alert is the email most often faked. The plainer a real one is, the easier a fake is to spot.'],
  ['Attention or urgent mail', 'A smiling mascot on an outage reads as not taking it seriously. The build enforces this one.'],
  ['"Resolved"', 'Good news, but about an outage. Same reason.'],
  ['Legal, billing, money', 'Formality is the point.'],
  ['Frequent notifications', 'Novelty on every task assignment becomes noise.'],
] as const;

// ── Components ──────────────────────────────────────────────────────────────────────────────────
export type Sample = {
  name: string;
  /** When to reach for it. */
  use: string;
  /** When not to. */
  avoid?: string;
  /** The props, in one line. */
  props?: string;
  mdx: string;
  /** Values for {{ fields }} in the rendered sample. */
  preview?: Record<string, string>;
};

export const SAMPLES: { group: string; intro: string; items: Sample[] }[] = [
  {
    group: 'Writing',
    intro: 'Plain Markdown. Each piece becomes an email-safe component, so there\'s nothing to import.',
    items: [
      {
        name: 'Paragraph',
        use: 'Most of any email. Short paragraphs — two or three sentences.',
        mdx: 'Paragraphs are plain Markdown. **Bold** for the one fact that matters, and [a link](https://help.servantium.com) where the reader might want more.',
      },
      {
        name: 'Section heading',
        use: 'Splitting a longer email into parts a reader can scan. `##` only.',
        avoid: '`#` — the banner already carries the headline.',
        mdx: '## What\'s changing\n\nA heading is followed by at least one paragraph.',
      },
      {
        name: 'Bulleted list',
        use: 'Three to five short, parallel items.',
        avoid: 'Lists of long paragraphs — use Items.',
        mdx: '- Drawn as a table, so bullets line up in Outlook\n- One line each, where you can\n- Numbered lists come out as bullets too',
      },
      {
        name: 'Divider',
        use: 'A hard break between two unrelated parts. Rarely needed — a heading usually does the job.',
        mdx: 'Above the line.\n\n---\n\nBelow the line.',
      },
      {
        name: 'Code',
        use: 'Internal and technical mail. Customers rarely need it.',
        mdx: '```\nPOSTMARK_TEMPLATE=incident\n```',
      },
    ],
  },
  {
    group: 'Actions',
    intro: 'One primary button per email. If there are two things to do, the second is a secondary button or a link.',
    items: [
      {
        name: 'Button — primary',
        use: 'The one action the email exists for.',
        avoid: 'Legal notices, where a filled green button reads as a sales pitch.',
        props: 'href · width (Outlook only — widen it for long labels)',
        mdx: '<Button href="https://app.servantium.com">Open Servantium</Button>',
      },
      {
        name: 'Button — secondary',
        use: 'A second action, or the only action on a notice or incident.',
        props: 'href · variant="secondary" · width',
        mdx: '<Button href="https://trust.servantium.com" variant="secondary" width={260}>View the sub-processor list</Button>',
      },
      {
        name: 'Link fallback',
        use: 'Under any button whose link carries a one-time code — resets, invitations. Some clients break buttons; a pasted link always works.',
        props: 'href',
        mdx: '<LinkFallback href="https://app.servantium.com/__/auth/action?mode=resetPassword&oobCode=Rt5nW2" />',
      },
    ],
  },
  {
    group: 'Data',
    intro: 'For facts a reader will look up rather than read.',
    items: [
      {
        name: 'Data table — panel',
        use: 'Details in the flow of a message: a task\'s dates, a quote\'s totals.',
        props: 'rows · title · labelWidth',
        mdx: '<DataTable title="Clinical sample manifest reconciliation" labelWidth={112} rows={[\n  ["Due", <b>Fri, Oct 16, 2026</b>],\n  ["Engagement", "AUR-417 — Phase II Immunogenicity & PK"],\n  ["Waiting on", "Project kickoff & study handoff"],\n]} />',
      },
      {
        name: 'Data table — outline',
        use: 'A record the reader will refer back to — a legal summary, an incident\'s timings.',
        props: 'variant="outline" · rows · labelWidth',
        mdx: '<DataTable variant="outline" labelWidth={136} rows={[\n  ["Effective date", <b>October 24, 2026</b>],\n  ["Action required", "None"],\n]} />',
      },
      {
        name: 'Items',
        use: 'A run of titled things — release highlights, onboarding steps, incident updates.',
        props: 'items: { title, body, chip?, meta? }[]',
        mdx: '<Items items={[\n  { chip: { tone: "default", label: "New" }, title: "Secure Search", body: "Search only shows records you\'re allowed to see." },\n  { chip: { tone: "attention", label: "Changed" }, meta: "Settings → Users", title: "User Management", body: "Click a person to assign roles and tags." },\n]} />',
      },
      {
        name: 'Chip',
        use: 'A one-word status beside a title: New, Changed, Resolved, Beta.',
        props: 'tone: default · attention · urgent · neutral',
        mdx: '<Chip>New</Chip> <Chip tone="attention">Changed</Chip> <Chip tone="urgent">Removed</Chip> <Chip tone="neutral">Beta</Chip>',
      },
    ],
  },
  {
    group: 'Emphasis',
    intro: 'A callout is for the one thing a reader must not miss. One per email; if everything is highlighted, nothing is. The tone fills the whole panel — there is no coloured bar down the side, and there never will be.',
    items: [
      {
        name: 'Callout',
        use: 'default: reassurance ("Didn\'t request this?"). attention: something to do. urgent: something to stop doing. neutral: a quoted note.',
        props: 'tone · title',
        mdx: '<Callout title="Didn\'t request this?">You can ignore this email. Your password won\'t change.</Callout>\n\n<Spacer size={12} />\n\n<Callout tone="attention" title="Before the window starts">Save any open quotes or plans.</Callout>\n\n<Spacer size={12} />\n\n<Callout tone="urgent" title="Don\'t share this code">Servantium will never ask you for it.</Callout>\n\n<Spacer size={12} />\n\n<Callout tone="neutral" title="Jules Hart wrote">“Flag anything outside the 10% tolerance.”</Callout>',
      },
      {
        name: 'Eyebrow',
        use: 'A breadcrumb above a heading or table title — a project code, a section.',
        mdx: '<Eyebrow>AUR-417 · Phase II</Eyebrow>\n\n## Clinical sample manifest reconciliation',
      },
      {
        name: 'Spacer',
        use: 'Space around components. Paragraphs space themselves; components don\'t.',
        props: 'size (px, default 24)',
        mdx: 'Text above.\n\n<Spacer size={32} />\n\nText 32px below.',
      },
    ],
  },
  {
    group: 'Merge fields',
    intro: 'Anything the sender fills in. Write {{ field_name }} anywhere — text, a component, the frontmatter. It reaches Postmark untouched; the gallery fills it from `preview`.',
    items: [
      {
        name: 'In text',
        use: 'Names, dates, anything specific to the reader.',
        mdx: 'Hi {{ first_name }}, your quote for **{{ client }}** is ready.',
        preview: { first_name: 'Jules', client: 'Aurora Pharmaceuticals' },
      },
      {
        name: 'In a component',
        use: 'Inside a component, a field is a string: "{{ field }}". To make it bold, {"{{ field }}"} inside the tag.',
        mdx: '<DataTable rows={[\n  ["Client", "{{ client }}"],\n  ["Due", <b>{"{{ due }}"}</b>],\n]} />\n\n<Spacer size={20} />\n\n<Button href="{{ quote_url }}">Open quote</Button>',
        preview: { client: 'Aurora Pharmaceuticals', due: 'Fri, Oct 16', quote_url: 'https://app.servantium.com' },
      },
    ],
  },
  {
    group: 'Optional and editable content',
    intro: 'Two building blocks that Postmark understands natively. No new system is needed to hide content that has no data, or to let an admin replace a paragraph later.',
    items: [
      {
        name: 'If — optional content',
        use: 'Content that should only appear when the sender supplies a field: a note, a reason, a comment. Inside, {{ . }} is that field’s value — Postmark scopes sections, so nothing else can be referenced inside.',
        props: 'field',
        mdx: '<If field="note">\n  <Callout tone="neutral" title="Their note">“{{ . }}”</Callout>\n</If>\n\nThe rest of the email.',
        preview: { note: 'Flag anything outside the 10% tolerance.' },
      },
      {
        name: 'Editable — a paragraph an admin can override',
        use: 'Copy a workspace admin might want to change later — an intro, a sign-off. The default shows until the sender passes a value for the field. Only text can change; the design can’t.',
        props: 'field',
        mdx: '<Editable field="welcome_intro">Your team uses Servantium to scope, price and deliver every project.</Editable>',
      },
      {
        name: 'Company link',
        use: 'Any link to a Servantium address in the body. The address comes from company.json, so moving the app or the trust centre updates every email. Buttons take `to` the same way.',
        props: 'to: website · app · help · privacy · terms · trust · releaseNotes',
        mdx: 'Sign in at <CompanyLink to="app" />.\n\n<Button to="trust" variant="secondary" width={250}>View the trust centre</Button>',
      },
    ],
  },
];

// ── Banned ──────────────────────────────────────────────────────────────────────────────────────
export const BANNED: { rule: string; why: string; enforced: boolean }[] = [
  { rule: 'A coloured bar down the left of a section', why: 'Design decision, 2026-09-24. Callouts carry their tone as a full tint.', enforced: true },
  { rule: 'Astro on attention or urgent mail', why: 'See Astro.', enforced: true },
  { rule: 'An unsubscribe link on transactional mail — or none on broadcast', why: 'Transactional mail must always arrive. Postmark requires one on broadcast.', enforced: true },
  { rule: 'SVG images', why: 'Gmail and Outlook drop them.', enforced: true },
  { rule: 'Flex or grid layout', why: 'Outlook desktop can\'t draw them. Everything is tables.', enforced: true },
  { rule: 'Images without alt text', why: 'Most Outlook users see alt text first; images are off by default.', enforced: true },
  { rule: 'Emails over 102 KB', why: 'Gmail cuts them off with "View entire message".', enforced: true },
  { rule: 'Addresses or footer links typed into an email', why: 'They come from company.json, so a change reaches every email.', enforced: true },
  { rule: 'More than one primary button', why: 'Two filled buttons compete; the reader picks neither.', enforced: true },
  { rule: 'Text in images', why: 'Invisible with images off, unreadable to screen readers, unsearchable.', enforced: false },
];
