/**
 * draft-release-notes — turn a month of help-site release notes into a draft email.
 *
 *   node scripts/draft-release-notes.mjs \
 *     --from ../../../servantium-help/src/content/docs/help/release-notes \
 *     --month 2026-06 \
 *     --pick "Secure Search,Contact Workspaces,Inline Custom Properties,Tag Entry Improvements"
 *
 * The release notes are WRITTEN ONCE, on the help site. The email is assembled from them, so the two
 * can never say different things and nobody writes the same paragraph twice.
 *
 * It drafts; a person edits. A month can hold forty-odd items (June 8 alone had 41), and an email
 * that lists them all gets skimmed and deleted. So the draft carries a handful of highlights —
 * `--pick` chooses them by title, otherwise the first four new features — counts the rest, and
 * links to the full notes. Every unpicked feature is listed in a comment at the foot of the draft
 * so the editor can swap one in.
 *
 * `upcoming-*.mdx` is skipped: it is the help site's in-testing page, and although its frontmatter
 * says `published` its first line says the changes haven't shipped. An email can't announce them.
 */
import { readFileSync, readdirSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { parse as parseYaml } from 'yaml';

const company = createRequire(import.meta.url)('@servantium/brand/company.json');

const HERE = dirname(fileURLToPath(import.meta.url));
const arg = (k) => { const i = process.argv.indexOf(`--${k}`); return i > -1 ? process.argv[i + 1] : undefined; };

const from = arg('from');
const month = arg('month');
if (!from || !/^\d{4}-\d{2}$/.test(month ?? '')) {
  console.error('usage: draft-release-notes.mjs --from <help release-notes dir> --month YYYY-MM [--pick "Title,Title"] [--out file]');
  process.exit(1);
}
const picks = (arg('pick') ?? '').split(',').map((s) => s.trim()).filter(Boolean);
const out = arg('out') ?? join(HERE, `../src/emails/release-notes-${month}.mdx`);

const monthName = new Date(`${month}-01T00:00:00Z`).toLocaleString('en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' });

// ── Read the month's published releases ─────────────────────────────────────────────────────────
const releases = readdirSync(from).filter((f) => f.endsWith('.mdx') && !f.startsWith('upcoming')).map((f) => {
  const src = readFileSync(join(from, f), 'utf8');
  const m = src.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
  return m ? { file: f, fm: parseYaml(m[1]), body: m[2] } : null;
}).filter((r) => r && String(r.fm.date ?? '').startsWith(month) && r.fm.status === 'published');

if (!releases.length) { console.error(`no published release notes for ${month} in ${from}`); process.exit(1); }

/** `- **Title**: body` under a given `## Heading`. */
const itemsUnder = (body, heading) => {
  const section = body.split(/^## /m).find((s) => s.startsWith(heading));
  if (!section) return [];
  return [...section.matchAll(/^- \*\*(.+?)\*\*:?\s*(.+)$/gm)].map(([, title, text]) => ({
    title: title.trim(),
    // Plain text: inline Markdown inside a component prop would print its asterisks and backticks.
    body: text.replace(/\*\*(.+?)\*\*/g, '$1').replace(/`(.+?)`/g, '$1').trim(),
  }));
};

const features = releases.flatMap((r) => itemsUnder(r.body, 'New Features'));
const fixes = releases.flatMap((r) => itemsUnder(r.body, 'Fixes'));

const chosen = picks.length
  ? picks.map((p) => features.find((f) => f.title.toLowerCase() === p.toLowerCase()) ?? (() => { throw new Error(`--pick "${p}" is not a ${month} feature`); })())
  : features.slice(0, 4);
const rest = features.filter((f) => !chosen.includes(f));
const more = rest.length + fixes.length;

// ── Write the draft ─────────────────────────────────────────────────────────────────────────────
const js = (s) => JSON.stringify(s);
const mdx = `---
sends: "Postmark template \`release-notes-${month}\`, broadcast stream. A monthly job sends it to active users in batches of 500; Postmark skips anyone who has unsubscribed."
subject: ${js(`What's new in Servantium — ${monthName}`)}
preheader: ${js(`${chosen.slice(0, 2).map((c) => c.title).join(', ')}, and ${more} more improvements.`)}
label: Release notes
title: What's new in Servantium
subtitle: ${js(monthName)}
astro: professor
stream: broadcast
footer:
  reason: You're receiving product updates because you're a Servantium user.
fields:
  first_name: { example: Jules, note: "From the user's profile" }
---
{/* DRAFT from ${releases.map((r) => r.file).join(', ')}. Edit freely; the help site stays the record. */}

Hi {{ first_name }},

Here are the highlights from ${monthName}.

<Items items={[
${chosen.map((c) => `  { chip: { tone: 'default', label: 'New' }, title: ${js(c.title)}, body: ${js(c.body)} },`).join('\n')}
]} />

Plus ${more} more improvements and fixes, all in the full release notes.

<Button href="${company.urls.releaseNotes}" width={260}>Read the full release notes</Button>

{/* Other ${month} features you could swap in:
${rest.map((r) => `  - ${r.title}`).join('\n')}
*/}
`;

mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, mdx);
console.log(`drafted ${out}\n  ${releases.length} release(s) · ${chosen.length} highlights · ${more} more`);
