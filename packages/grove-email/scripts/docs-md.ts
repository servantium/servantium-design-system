/**
 * The two generated docs, for GitHub. Both are written by the build and checked by the tests, so
 * what people read can't drift from the code:
 *   docs/style-guide.md  from src/stylesheet.ts, the same source as dist/stylesheet.html
 *   docs/templates.md    from the emails' frontmatter: every template and the data it needs
 */
import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  ACCESSIBILITY, BANNED, FRONTMATTER, FRONTMATTER_EXAMPLE, SAMPLES, TONE_GUIDE, TONE_QUESTION, WRITING,
} from '../src/stylesheet';
import type { Tone } from '../src/theme';
import { isList } from '../src/mdx';
import type { Built } from './collect';

const COMPONENTS = join(dirname(fileURLToPath(import.meta.url)), '../src/components');

/** Samples written in plain Markdown, and the component each one becomes. */
export const MARKDOWN: Record<string, string> = {
  Paragraph: 'Text', Link: 'Link', 'Section heading': 'Heading', 'Bulleted list': 'List', Divider: 'Divider', Code: 'CodeBlock',
};

/** Samples about a technique, not one component. */
const NO_SOURCE = new Set(['In text', 'In a component']);

const sourceOf = (name: string, mdx: string) => {
  if (NO_SOURCE.has(name)) return undefined;
  const c = MARKDOWN[name] ?? /<([A-Z]\w+)/.exec(mdx)?.[1];
  return c && existsSync(join(COMPONENTS, `${c}.tsx`)) ? c : undefined;
};
const anchor = (s: string) => s.toLowerCase().replace(/[^a-z0-9 -]/g, '').trim().replace(/\s+/g, '-');
const cell = (s: string) => s.replace(/\|/g, '\\|').replace(/\n/g, ' ');

export function styleGuideMarkdown(): string {
  const out: string[] = [];
  out.push(`# Email style guide

<!-- GENERATED from src/stylesheet.ts by \`npm run build\`. Edit that file, not this one; \`npm test\` fails if this page is stale. -->

Everything an email may contain, and the rules each one follows. The same content, rendered, is \`dist/stylesheet.html\` after a build. For the walk-through of writing a new email, start with [writing-an-email.md](./writing-an-email.md).

- [Frontmatter](#frontmatter)
- [Tones](#tones)
${SAMPLES.map((g) => `- [${g.group}](#${anchor(g.group)})`).join('\n')}
- [Writing rules](#writing-rules)
- [Accessibility](#accessibility)
- [Banned](#banned)
`);

  out.push(`## Frontmatter

The block at the top of a master builds the frame (banner, footer, stream) and declares the data the email needs. It's validated like a schema: a broken rule fails the build with a sentence.

| Key | | Values | Notes |
|---|---|---|---|
${FRONTMATTER.map((f) => `| \`${f.field}\` | ${f.required ? 'required' : 'optional'} | ${cell(f.values)} | ${cell(f.note)} |`).join('\n')}

\`\`\`mdx
${FRONTMATTER_EXAMPLE}
\`\`\`
`);

  out.push(`## Tones

One question: **${TONE_QUESTION}** The banner never changes; a tone colours the dot beside the label, the rule under the banner, and any callout.

| Tone | Answer | Use it for | Examples |
|---|---|---|---|
${(Object.keys(TONE_GUIDE) as Tone[]).map((t) => `| \`${t}\` | ${cell(TONE_GUIDE[t].answer)} | ${cell(TONE_GUIDE[t].use)} | ${cell(TONE_GUIDE[t].examples)} |`).join('\n')}
`);

  for (const g of SAMPLES) {
    out.push(`## ${g.group}\n\n${g.intro}\n`);
    for (const s of g.items) {
      const src = sourceOf(s.name, s.mdx);
      out.push(`### ${s.name}\n`);
      out.push(`${s.use}\n`);
      if (s.avoid) out.push(`**Not for:** ${s.avoid}\n`);
      if (s.props) out.push(`**Props:** ${s.props}\n`);
      if (src) out.push(`**Source:** [\`src/components/${src}.tsx\`](../src/components/${src}.tsx)\n`);
      out.push(`\`\`\`mdx\n${s.mdx}\n\`\`\`\n`);
    }
  }

  out.push(`## Writing rules

| Rule | In practice |
|---|---|
${WRITING.map(([r, ex]) => `| **${cell(r)}** | ${cell(ex)} |`).join('\n')}
`);

  out.push(`## Accessibility

| | |
|---|---|
${ACCESSIBILITY.map(([r, how]) => `| **${cell(r)}** | ${cell(how)} |`).join('\n')}
`);

  out.push(`## Banned

"Enforced" means \`npm test\` fails; "review" means a person checks it in the pull request.

| Rule | | Why |
|---|---|---|
${BANNED.map((b) => `| ${cell(b.rule)} | ${b.enforced ? 'enforced' : 'review'} | ${cell(b.why)} |`).join('\n')}
`);

  return `${out.join('\n').trim()}\n`;
}

// ── The template catalogue ──────────────────────────────────────────────────────────────────────
const ex = (s: string) => (s.length > 90 ? `${s.slice(0, 87)}…` : s);

export function templatesMarkdown(emails: Built[]): string {
  const out: string[] = [`# Email templates

<!-- GENERATED from src/emails/*.mdx by \`npm run build\`. Edit the masters, not this page; \`npm test\` fails if it's stale. -->

Every email, with the data its sender supplies. The alias is the Postmark template alias and the master's file name. Streams are Postmark's: \`outbound\` for transactional mail, \`broadcast\` for mail people can unsubscribe from. Every email is sent from \`Servantium <notifications@servantium.com>\` with Reply-To \`help@servantium.com\` unless its notes say otherwise. How to name and format values: [fields.md](./fields.md).

| Alias | Name | Stream | Fields |
|---|---|---|---|
${emails.map((e) => `| [\`${e.id}\`](#${e.id}) | ${cell(e.name)} | ${e.stream === 'broadcast' ? 'broadcast' : 'outbound'} | ${Object.keys(e.fields).length} |`).join('\n')}
`];

  for (const e of emails) {
    const fm = e.frontmatter;
    out.push(`## ${e.id}

**${cell(e.name)}** · [\`src/emails/${e.id}.mdx\`](../src/emails/${e.id}.mdx)

${e.sends}

| | |
|---|---|
| Stream | ${e.stream === 'broadcast' ? '`broadcast`' : '`outbound`'} |
| Subject | \`${cell(fm.subject)}\` |
| Preheader | \`${cell(fm.preheader)}\` |
| Banner | ${cell(fm.label)} · “${cell(fm.title)}” · ${fm.tone} tone |
| Footer reason | ${cell(fm.footer.reason)} |

| Field | | Note | Example |
|---|---|---|---|
${Object.entries(e.fields).map(([name, f]) => {
      const kind = isList(f)
        ? `list of { ${[...new Set(f.example.flatMap((i) => Object.keys(i)))].join(', ')} }`
        : 'text';
      const example = isList(f) ? `${f.example.length} items, e.g. ${ex(Object.values(f.example[0]).join(' · '))}` : ex(f.example as string);
      return `| \`${name}\` | ${kind}${f.optional ? ', optional' : ''} | ${cell(f.note ?? '')} | ${cell(example)} |`;
    }).join('\n')}
`);
  }
  return `${out.join('\n').trim()}\n`;
}
