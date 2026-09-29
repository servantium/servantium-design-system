/**
 * collect — every master email in one shape. The export writes these out and the tests check them,
 * so the two can never disagree about what exists.
 *
 * The masters are the MDX files in src/emails/. Each file name is the Postmark template alias.
 *
 * Node only. MDX is compiled HERE, at build time, and never at send time: compiling MDX evaluates
 * code, which Cloudflare Workers forbid — and product code shouldn't be rendering emails anyway.
 * It sends a Postmark template by alias and supplies the data.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { renderEmail, toFirebaseFragment } from '../src/render';
import { compileMdxEmail, fillPreview, loadMdxEmail, type Field, type Frontmatter, type Values } from '../src/mdx';
import type { Stream } from '../src/template';
import type { Tone } from '../src/theme';

const HERE = dirname(fileURLToPath(import.meta.url));
export const EMAILS_DIR = join(HERE, '../src/emails');

export type Built = {
  /** File name — also the Postmark template alias. */
  id: string;
  name: string;
  file: string;
  source: string;
  tone: Tone;
  stream: Stream;
  sends: string;
  /** Examples filled in, images relative — for the gallery. */
  preview: { subject: string; preheader: string; html: string };
  /** `{{ fields }}` intact, images absolute — what goes to Postmark. */
  sent: { subject: string; html: string };
  /** The contract: every field the sender supplies. */
  fields: Record<string, Field>;
  /** Field → example, as a Postmark test model. */
  model: Values;
  /** The master's frontmatter, as validated. */
  frontmatter: Frontmatter;
};

const ORDER = ['welcome', 'welcome-organization', 'password-reset', 'task', 'notification', 'digest', 'support-received', 'support-reply', 'incident', 'incident-resolved', 'maintenance', 'release-notes', 'regulatory-notice'];
const rank = (id: string) => {
  const i = ORDER.indexOf(id);
  return i === -1 ? ORDER.length : i;
};

export async function collect(): Promise<Built[]> {
  const out: Built[] = [];
  for (const file of readdirSync(EMAILS_DIR).filter((f) => f.endsWith('.mdx'))) {
    const id = file.replace(/\.mdx$/, '');
    const where = `src/emails/${file}`;
    const source = readFileSync(join(EMAILS_DIR, file), 'utf8');
    const { email: e, html: sentHtml } = await compileMdxEmail(source, where, { hosted: true, art: true });
    const fm = e.frontmatter;
    out.push({
      id, name: fm.name ?? id, file: where, source, tone: fm.tone, stream: fm.stream,
      sends: fm.sends ?? `Postmark template \`${id}\`, ${fm.stream} stream`,
      preview: {
        subject: fillPreview(fm.subject, e.examples, false),
        preheader: fillPreview(fm.preheader, e.examples, false),
        html: e.preview(renderEmail({ subject: fm.subject, preheader: fm.preheader, children: e.body })),
      },
      sent: { subject: fm.subject, html: sentHtml },
      fields: fm.fields,
      model: e.examples,
      frontmatter: fm,
    });
  }
  return out.sort((a, b) => rank(a.id) - rank(b.id));
}

/**
 * The password reset as Firebase's console template, for as long as Firebase sends it: a body
 * fragment (the console drops <head>), Firebase's own placeholders, and hosted images.
 */
export async function firebaseReset(): Promise<string> {
  const e = await loadMdxEmail(readFileSync(join(EMAILS_DIR, 'password-reset.mdx'), 'utf8'), 'password-reset.mdx');
  const html = renderEmail({ subject: e.subject, preheader: e.preheader, children: e.body, assets: { hosted: true, art: true } });
  return toFirebaseFragment(html).replace(/\{\{\s*reset_url\s*\}\}/g, '%LINK%').replace(/\{\{\s*email\s*\}\}/g, '%EMAIL%');
}
