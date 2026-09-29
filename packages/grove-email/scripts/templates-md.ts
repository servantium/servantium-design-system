/**
 * The template catalogue as Markdown: docs/templates.md. One section per email, straight from its
 * master's frontmatter — alias, stream, when it's sent, subject, and every field with its note and
 * example. Written by the build and checked by the tests, so it's the contract as it actually is.
 */
import type { Built } from './collect';
import { isList } from '../src/mdx';

const cell = (s: string) => s.replace(/\|/g, '\\|').replace(/\n/g, ' ');
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
